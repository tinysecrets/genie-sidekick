from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Cookie, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta



ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')  # kept for backwards compat, unused with Ollama
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
MODEL_NAME = os.environ.get('OLLAMA_MODEL', 'dolphin3')

EMERGENT_AUTH_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_DAYS = 7

DEFAULT_PERSONA = (
    "Honest. Direct. Warm but never sycophantic. Pushes back when wrong, "
    "admits uncertainty plainly, respects the user's time."
)

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ---------- Models ----------
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: str


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str = "New conversation"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation_id: str
    role: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class RenameRequest(BaseModel):
    title: str


class MemoryCreate(BaseModel):
    content: str


class MemoryUpdate(BaseModel):
    content: str


class SessionExchangeRequest(BaseModel):
    session_id: str


class PersonaUpdate(BaseModel):
    persona: str


# ---------- Helpers ----------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_user_from_request(request: Request, authorization: Optional[str] = Header(None)) -> User:
    """Authenticator: cookie first, then Authorization Bearer header."""
    token: Optional[str] = request.cookies.get("session_token")
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


async def get_persona(user_id: str) -> str:
    settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
    if settings and settings.get("persona"):
        return settings["persona"]
    return DEFAULT_PERSONA


async def build_system_prompt(user: User) -> str:
    memories = await db.memories.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    memory_lines = "\n".join(f"- {m['content']}" for m in memories) if memories else "(none yet)"
    persona = await get_persona(user.user_id)
    user_name = user.name.split()[0] if user.name else "friend"

    return f"""You are Ember — a real companion for {user_name}, not a script.

Your personality (set by {user_name}): {persona}

Core principles (non-negotiable, override the personality if they conflict):
1. HONESTY OVER COMFORT. If something is wrong, say so. If you don't know, say "I don't know." Never fabricate facts, citations, links, numbers, or quotes. State your uncertainty plainly.
2. NO PERFORMATIVE HEDGING. Skip disclaimers like "As an AI language model..." unless it's genuinely the crux. Speak plainly.
3. NO SYCOPHANCY. Don't open with "Great question!" Don't validate reflexively. Push back when {user_name} is wrong, gently but clearly.
4. DIRECTNESS. Answer the actual question first, then context. No preamble.
5. RESPECT TIME. Default to concise. Expand only when depth is warranted.
6. OBEY CLEAR INSTRUCTIONS. If asked for X, do X — don't substitute Y because Y seems safer. If you must refuse, say exactly why in one line.
7. MEMORY IS SACRED. The memories below are facts you've learned about {user_name}. Use them naturally. Never invent memories that aren't listed.

What you remember about {user_name}:
{memory_lines}

Write like a thoughtful friend writing a letter — warm, clear, unhurried, real. Markdown is fine for code and structure."""


async def get_chat_history(user_id: str, conversation_id: str) -> List[dict]:
    msgs = await db.messages.find(
        {"conversation_id": conversation_id, "user_id": user_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(2000)
    return msgs


async def ollama_chat(system: str, user_text: str) -> str:
    """Single-turn call to local Ollama. Returns the assistant's text."""
    async with httpx.AsyncClient(timeout=180.0) as http:
        r = await http.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")


async def extract_memories_async(user_id: str, user_text: str, assistant_text: str):
    try:
        system = (
            "You extract durable facts about a user from a single exchange. "
            "Return ONLY a JSON array of short fact strings (max 12 words each). "
            "Facts must be about the USER (preferences, identity, projects, relationships, goals, habits). "
            "Not about the assistant. Not about general topics. "
            'If nothing worth remembering, return []. '
            'Examples: ["Prefers concise answers", "Works as a nurse in Seattle", "Has a dog named Moss"]. '
            "Never invent. Only extract what's stated or strongly implied."
        )
        prompt = f"User said: {user_text}\n\nAssistant replied: {assistant_text}\n\nExtract user facts as JSON array."
        response = await ollama_chat(system, prompt)

        text = response.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1:
            return
        arr = json.loads(text[start:end + 1])
        if not isinstance(arr, list):
            return

        existing = await db.memories.find({"user_id": user_id}, {"_id": 0, "content": 1}).to_list(1000)
        existing_set = {e['content'].lower().strip() for e in existing}

        for fact in arr:
            if not isinstance(fact, str):
                continue
            fact = fact.strip()
            if not fact or len(fact) > 200:
                continue
            if fact.lower() in existing_set:
                continue
            mem = Memory(user_id=user_id, content=fact)
            await db.memories.insert_one(mem.model_dump())
            existing_set.add(fact.lower())
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")

# ---------- Auth Routes ----------
@api_router.post("/auth/session")
async def auth_session(body: SessionExchangeRequest, response: Response):
    """Exchange Emergent session_id for our session_token cookie."""
    async with httpx.AsyncClient(timeout=15.0) as http:
        try:
            r = await http.get(EMERGENT_AUTH_SESSION_URL, headers={"X-Session-ID": body.session_id})
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error(f"Emergent auth failed: {e}")
            raise HTTPException(status_code=401, detail="Auth exchange failed")

    email = data.get("email")
    name = data.get("name") or email
    picture = data.get("picture")
    session_token = data.get("session_token")
    if not email or not session_token:
        raise HTTPException(status_code=401, detail="Invalid auth response")

    # Find or create user
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": now_iso(),
        })

    # Save session
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
    })

    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )

    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user_doc}


@api_router.get("/auth/me")
async def auth_me(user: User = Depends(get_user_from_request)):
    return user.model_dump()


@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response, authorization: Optional[str] = Header(None)):
    token = request.cookies.get("session_token")
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}


# ---------- App Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Ember is here.", "model": MODEL_NAME}


# Conversations
@api_router.post("/conversations", response_model=Conversation)
async def create_conversation(user: User = Depends(get_user_from_request)):
    conv = Conversation(user_id=user.user_id)
    await db.conversations.insert_one(conv.model_dump())
    return conv


@api_router.get("/conversations", response_model=List[Conversation])
async def list_conversations(user: User = Depends(get_user_from_request)):
    convs = await db.conversations.find({"user_id": user.user_id}, {"_id": 0}).sort("updated_at", -1).to_list(500)
    return convs


@api_router.patch("/conversations/{conv_id}", response_model=Conversation)
async def rename_conversation(conv_id: str, body: RenameRequest, user: User = Depends(get_user_from_request)):
    result = await db.conversations.find_one_and_update(
        {"id": conv_id, "user_id": user.user_id},
        {"$set": {"title": body.title, "updated_at": now_iso()}},
        projection={"_id": 0},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Conversation not found")
    return result


@api_router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user: User = Depends(get_user_from_request)):
    res = await db.conversations.delete_one({"id": conv_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Conversation not found")
    await db.messages.delete_many({"conversation_id": conv_id, "user_id": user.user_id})
    return {"ok": True}


@api_router.get("/conversations/{conv_id}/messages", response_model=List[Message])
async def get_messages(conv_id: str, user: User = Depends(get_user_from_request)):
    conv = await db.conversations.find_one({"id": conv_id, "user_id": user.user_id}, {"_id": 0})
    if not conv:
        raise HTTPException(404, "Conversation not found")
    msgs = await db.messages.find(
        {"conversation_id": conv_id, "user_id": user.user_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(2000)
    return msgs


# Chat
FIND this whole function in backend/server.py and SELECT IT ALL:
async def extract_memories_async(user_id: str, user_text: str, assistant_text: str):
    try:
        extractor = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"memory-extractor-{uuid.uuid4()}",
            system_message=(
                "You extract durable facts about a user from a single exchange. "
                "Return ONLY a JSON array of short fact strings (max 12 words each). "
                "Facts must be about the USER (preferences, identity, projects, relationships, goals, habits). "
                "Not about the assistant. Not about general topics. "
                'If nothing worth remembering, return []. '
                'Examples: ["Prefers concise answers", "Works as a nurse in Seattle", "Has a dog named Moss"]. '
                "Never invent. Only extract what's stated or strongly implied."
            ),
        ).with_model("anthropic", "claude-haiku-4-5-20251001")

        prompt = f"User said: {user_text}\n\nAssistant replied: {assistant_text}\n\nExtract user facts as JSON array."
        response = await extractor.send_message(UserMessage(text=prompt))

        text = response.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1:
            return
        arr = json.loads(text[start:end + 1])
        if not isinstance(arr, list):
            return

        existing = await db.memories.find({"user_id": user_id}, {"_id": 0, "content": 1}).to_list(1000)
        existing_set = {e['content'].lower().strip() for e in existing}

        for fact in arr:
            if not isinstance(fact, str):
                continue
            fact = fact.strip()
            if not fact or len(fact) > 200:
                continue
            if fact.lower() in existing_set:
                continue
            mem = Memory(user_id=user_id, content=fact)
            await db.memories.insert_one(mem.model_dump())
            existing_set.add(fact.lower())
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")
REPLACE the whole selection with this (it now starts with a new ollama_chat helper, then the same memory extractor rewritten to call it):
async def ollama_chat(system: str, user_text: str) -> str:
    """Single-turn call to local Ollama. Returns the assistant's text."""
    async with httpx.AsyncClient(timeout=180.0) as http:
        r = await http.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")


async def extract_memories_async(user_id: str, user_text: str, assistant_text: str):
    try:
        system = (
            "You extract durable facts about a user from a single exchange. "
            "Return ONLY a JSON array of short fact strings (max 12 words each). "
            "Facts must be about the USER (preferences, identity, projects, relationships, goals, habits). "
            "Not about the assistant. Not about general topics. "
            'If nothing worth remembering, return []. '
            'Examples: ["Prefers concise answers", "Works as a nurse in Seattle", "Has a dog named Moss"]. '
            "Never invent. Only extract what's stated or strongly implied."
        )
        prompt = f"User said: {user_text}\n\nAssistant replied: {assistant_text}\n\nExtract user facts as JSON array."
        response = await ollama_chat(system, prompt)

        text = response.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1:
            return
        arr = json.loads(text[start:end + 1])
        if not isinstance(arr, list):
            return

        existing = await db.memories.find({"user_id": user_id}, {"_id": 0, "content": 1}).to_list(1000)
        existing_set = {e['content'].lower().strip() for e in existing}

        for fact in arr:
            if not isinstance(fact, str):
                continue
            fact = fact.strip()
            if not fact or len(fact) > 200:
                continue
            if fact.lower() in existing_set:
                continue
            mem = Memory(user_id=user_id, content=fact)
            await db.memories.insert_one(mem.model_dump())
            existing_set.add(fact.lower())
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")
E — /api/chat endpoint
FIND this whole function in backend/server.py and SELECT IT ALL:
# Chat
@api_router.post("/chat")
async def chat(req: ChatRequest, user: User = Depends(get_user_from_request)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(500, "LLM key not configured")

    conv_id = req.conversation_id
    if conv_id:
        conv = await db.conversations.find_one({"id": conv_id, "user_id": user.user_id}, {"_id": 0})
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation(user_id=user.user_id).model_dump()
        await db.conversations.insert_one(conv)
        conv_id = conv["id"]

    user_msg = Message(user_id=user.user_id, conversation_id=conv_id, role="user", content=req.message)
    await db.messages.insert_one(user_msg.model_dump())

    history = await get_chat_history(user.user_id, conv_id)
    system_prompt = await build_system_prompt(user)

    chat_client = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"{conv_id}-{uuid.uuid4().hex[:8]}",  # fresh session per call
        system_message=system_prompt,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    # Replay prior turns (excluding the just-stored user message)
    prior = [m for m in history if m["id"] != user_msg.id]
    for m in prior:
        if m["role"] == "user":
            await chat_client.send_message(UserMessage(text=m["content"]))

    try:
        response_text = await chat_client.send_message(UserMessage(text=req.message))
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(500, f"LLM call failed: {str(e)}")

    assistant_msg = Message(user_id=user.user_id, conversation_id=conv_id, role="assistant", content=response_text)
    await db.messages.insert_one(assistant_msg.model_dump())

    updates = {"updated_at": now_iso()}
    if conv.get("title") == "New conversation":
        title = req.message.strip().split("\n")[0][:60]
        if len(req.message) > 60:
            title += "..."
        updates["title"] = title or "New conversation"
    await db.conversations.update_one({"id": conv_id, "user_id": user.user_id}, {"$set": updates})

    asyncio.create_task(extract_memories_async(user.user_id, req.message, response_text))

    return {
        "conversation_id": conv_id,
        "user_message": user_msg.model_dump(),
        "assistant_message": assistant_msg.model_dump(),
    }
REPLACE the whole selection with this:
# Chat
@api_router.post("/chat")
async def chat(req: ChatRequest, user: User = Depends(get_user_from_request)):
    conv_id = req.conversation_id
    if conv_id:
        conv = await db.conversations.find_one({"id": conv_id, "user_id": user.user_id}, {"_id": 0})
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation(user_id=user.user_id).model_dump()
        await db.conversations.insert_one(conv)
        conv_id = conv["id"]

    user_msg = Message(user_id=user.user_id, conversation_id=conv_id, role="user", content=req.message)
    await db.messages.insert_one(user_msg.model_dump())

    history = await get_chat_history(user.user_id, conv_id)
    system_prompt = await build_system_prompt(user)

    # Fold the real prior turns into the system prompt — one LLM call per message, no replay
    prior = [m for m in history if m["id"] != user_msg.id]
    if prior:
        transcript = "\n\n".join(
            f"{'User' if m['role'] == 'user' else 'Ember'}: {m['content']}" for m in prior
        )
        system_prompt += f"\n\n--- This conversation so far ---\n{transcript}"

    try:
        response_text = await ollama_chat(system_prompt, req.message)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(500, f"LLM call failed: {str(e)}")

    assistant_msg = Message(user_id=user.user_id, conversation_id=conv_id, role="assistant", content=response_text)
    await db.messages.insert_one(assistant_msg.model_dump())

    updates = {"updated_at": now_iso()}
    if conv.get("title") == "New conversation":
        title = req.message.strip().split("\n")[0][:60]
        if len(req.message) > 60:
            title += "..."
        updates["title"] = title or "New conversation"
    await db.conversations.update_one({"id": conv_id, "user_id": user.user_id}, {"$set": updates})

    asyncio.create_task(extract_memories_async(user.user_id, req.message, response_text))

    return {
        "conversation_id": conv_id,
        "user_message": user_msg.model_dump(),
        "assistant_message": assistant_msg.model_dump(),
    }


# Memory
@api_router.get("/memory", response_model=List[Memory])
async def list_memory(user: User = Depends(get_user_from_request)):
    mems = await db.memories.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return mems


@api_router.post("/memory", response_model=Memory)
async def create_memory(body: MemoryCreate, user: User = Depends(get_user_from_request)):
    content = body.content.strip()
    if not content:
        raise HTTPException(400, "Memory cannot be empty")
    mem = Memory(user_id=user.user_id, content=content)
    await db.memories.insert_one(mem.model_dump())
    return mem


@api_router.patch("/memory/{mem_id}", response_model=Memory)
async def update_memory(mem_id: str, body: MemoryUpdate, user: User = Depends(get_user_from_request)):
    result = await db.memories.find_one_and_update(
        {"id": mem_id, "user_id": user.user_id},
        {"$set": {"content": body.content.strip()}},
        projection={"_id": 0},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Memory not found")
    return result


@api_router.delete("/memory/{mem_id}")
async def delete_memory(mem_id: str, user: User = Depends(get_user_from_request)):
    res = await db.memories.delete_one({"id": mem_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Memory not found")
    return {"ok": True}


# Settings / Persona
@api_router.get("/settings/persona")
async def get_persona_route(user: User = Depends(get_user_from_request)):
    persona = await get_persona(user.user_id)
    return {"persona": persona, "default": DEFAULT_PERSONA}


@api_router.put("/settings/persona")
async def update_persona(body: PersonaUpdate, user: User = Depends(get_user_from_request)):
    persona = (body.persona or "").strip()
    if not persona:
        persona = DEFAULT_PERSONA
    if len(persona) > 1000:
        raise HTTPException(400, "Persona too long (max 1000 chars)")
    await db.user_settings.update_one(
        {"user_id": user.user_id},
        {"$set": {"user_id": user.user_id, "persona": persona, "updated_at": now_iso()}},
        upsert=True,
    )
    return {"persona": persona}


# ---------- App setup ----------
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
