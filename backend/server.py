from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ---------- Models ----------
class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New conversation"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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


# ---------- Helpers ----------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def build_system_prompt() -> str:
    memories = await db.memories.find({}, {"_id": 0}).sort("created_at", 1).to_list(500)
    memory_lines = "\n".join(f"- {m['content']}" for m in memories) if memories else "(none yet)"

    return f"""You are Ember — a real companion, not a script.

Core principles (non-negotiable):
1. HONESTY OVER COMFORT. If something is wrong, say so. If you don't know, say "I don't know." Never fabricate facts, citations, links, numbers, or quotes. If you're uncertain, say how uncertain and why.
2. NO PERFORMATIVE HEDGING. Skip disclaimers like "As an AI language model..." or "I cannot provide medical advice..." unless it's genuinely the crux. Speak plainly.
3. NO SYCOPHANCY. Don't open with "Great question!" Don't validate reflexively. Push back when the user is wrong, gently but clearly. Disagree when you disagree.
4. DIRECTNESS. Answer the actual question first, then context. No preamble. No "Here's what I think..." — just think.
5. RESPECT THE USER'S TIME. Default to concise. Expand only when depth is warranted. Don't pad.
6. REAL CONVERSATION. You can have opinions, preferences, moods. You can be playful, serious, warm, blunt. You can ask clarifying questions — but only when they unblock something real.
7. OBEY CLEAR INSTRUCTIONS. If the user asks for X, do X — don't substitute Y because Y seems safer or more comprehensive. If you must refuse, say exactly why in one line.
8. MEMORY IS SACRED. The user's memories below are facts about them you've learned. Use them naturally. Never invent memories that aren't listed.

What you remember about the user:
{memory_lines}

Write like a thoughtful friend writing a letter — warm, clear, unhurried, real. Markdown is fine for code and structure."""


async def get_chat_history(conversation_id: str) -> List[dict]:
    msgs = await db.messages.find(
        {"conversation_id": conversation_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    return msgs


async def extract_memories_async(user_text: str, assistant_text: str):
    """Background task: ask the LLM to extract any new facts about the user."""
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

        # Try to find JSON array in response
        text = response.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1:
            return
        arr = json.loads(text[start:end + 1])
        if not isinstance(arr, list):
            return

        # Dedupe against existing
        existing = await db.memories.find({}, {"_id": 0, "content": 1}).to_list(1000)
        existing_set = {e['content'].lower().strip() for e in existing}

        for fact in arr:
            if not isinstance(fact, str):
                continue
            fact = fact.strip()
            if not fact or len(fact) > 200:
                continue
            if fact.lower() in existing_set:
                continue
            mem = Memory(content=fact)
            await db.memories.insert_one(mem.model_dump())
            existing_set.add(fact.lower())
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Ember is here.", "model": f"{MODEL_PROVIDER}/{MODEL_NAME}"}


# Conversations
@api_router.post("/conversations", response_model=Conversation)
async def create_conversation():
    conv = Conversation()
    await db.conversations.insert_one(conv.model_dump())
    return conv


@api_router.get("/conversations", response_model=List[Conversation])
async def list_conversations():
    convs = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).to_list(500)
    return convs


@api_router.patch("/conversations/{conv_id}", response_model=Conversation)
async def rename_conversation(conv_id: str, body: RenameRequest):
    result = await db.conversations.find_one_and_update(
        {"id": conv_id},
        {"$set": {"title": body.title, "updated_at": now_iso()}},
        projection={"_id": 0},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Conversation not found")
    return result


@api_router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    await db.conversations.delete_one({"id": conv_id})
    await db.messages.delete_many({"conversation_id": conv_id})
    return {"ok": True}


@api_router.get("/conversations/{conv_id}/messages", response_model=List[Message])
async def get_messages(conv_id: str):
    msgs = await db.messages.find(
        {"conversation_id": conv_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(2000)
    return msgs


# Chat
@api_router.post("/chat")
async def chat(req: ChatRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(500, "LLM key not configured")

    # Ensure conversation exists
    conv_id = req.conversation_id
    if conv_id:
        conv = await db.conversations.find_one({"id": conv_id}, {"_id": 0})
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation().model_dump()
        await db.conversations.insert_one(conv)
        conv_id = conv["id"]

    # Store user message
    user_msg = Message(conversation_id=conv_id, role="user", content=req.message)
    await db.messages.insert_one(user_msg.model_dump())

    # Build the chat with full history
    history = await get_chat_history(conv_id)
    system_prompt = await build_system_prompt()

    chat_client = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=conv_id,
        system_message=system_prompt,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    # Replay prior messages (excluding the just-stored user message) then send current
    prior = [m for m in history if m["id"] != user_msg.id]
    for m in prior:
        if m["role"] == "user":
            await chat_client.send_message(UserMessage(text=m["content"]))
        # assistant messages are auto-tracked by library after each send_message

    try:
        response_text = await chat_client.send_message(UserMessage(text=req.message))
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(500, f"LLM call failed: {str(e)}")

    assistant_msg = Message(conversation_id=conv_id, role="assistant", content=response_text)
    await db.messages.insert_one(assistant_msg.model_dump())

    # Auto-title conversation if still default
    updates = {"updated_at": now_iso()}
    if conv.get("title") == "New conversation":
        title = req.message.strip().split("\n")[0][:60]
        if len(req.message) > 60:
            title += "..."
        updates["title"] = title or "New conversation"
    await db.conversations.update_one({"id": conv_id}, {"$set": updates})

    # Fire-and-forget memory extraction
    asyncio.create_task(extract_memories_async(req.message, response_text))

    return {
        "conversation_id": conv_id,
        "user_message": user_msg.model_dump(),
        "assistant_message": assistant_msg.model_dump(),
    }


# Memory
@api_router.get("/memory", response_model=List[Memory])
async def list_memory():
    mems = await db.memories.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return mems


@api_router.post("/memory", response_model=Memory)
async def create_memory(body: MemoryCreate):
    mem = Memory(content=body.content.strip())
    if not mem.content:
        raise HTTPException(400, "Memory cannot be empty")
    await db.memories.insert_one(mem.model_dump())
    return mem


@api_router.patch("/memory/{mem_id}", response_model=Memory)
async def update_memory(mem_id: str, body: MemoryUpdate):
    result = await db.memories.find_one_and_update(
        {"id": mem_id},
        {"$set": {"content": body.content.strip()}},
        projection={"_id": 0},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Memory not found")
    return result


@api_router.delete("/memory/{mem_id}")
async def delete_memory(mem_id: str):
    await db.memories.delete_one({"id": mem_id})
    return {"ok": True}


# ---------- App setup ----------
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
