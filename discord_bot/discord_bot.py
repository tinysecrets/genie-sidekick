"""
Genie Discord Bot Bridge — DM @genie from your phone, get answers via /api/genie/chat.

Setup (5 min):
1. Create a Discord bot at https://discord.com/developers/applications
   - New Application → Bot tab → Reset Token → copy token
   - Bot tab → enable "MESSAGE CONTENT INTENT" (otherwise DMs won't deliver)
2. Get the bot's invite URL:
   - OAuth2 → URL Generator → scopes: `bot`, `applications.commands`
   - Bot permissions: Send Messages, Read Message History
   - Open the generated URL in a browser, add to your personal server (or just DM the bot directly)
3. Set env vars in a .env file next to this script:
       DISCORD_BOT_TOKEN=...
       GENIE_API_URL=https://genie.wah-lah.com
       GENIE_ADMIN_EMAIL=Jrs092393@gmail.com
       GENIE_ADMIN_PASSWORD=...your password...
       ALLOWED_DISCORD_USER_IDS=123456789  (comma-separated; only YOU can chat)
4. Run: pip install -r requirements.txt && python discord_bot.py
   Or deploy as a tiny Fly app — see Dockerfile in this folder.

The bot DMs Genie when you DM it. Group chats are ignored (this is YOUR sidekick).
"""

import asyncio
import logging
import os
from typing import Optional

import discord
import httpx
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("genie-bot")

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GENIE_API = os.environ.get("GENIE_API_URL", "https://genie.wah-lah.com").rstrip("/")
GENIE_EMAIL = os.environ["GENIE_ADMIN_EMAIL"]
GENIE_PASSWORD = os.environ["GENIE_ADMIN_PASSWORD"]
ALLOWED_USERS = {int(x.strip()) for x in os.environ.get("ALLOWED_DISCORD_USER_IDS", "").split(",") if x.strip().isdigit()}

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = discord.Client(intents=intents)
session_per_user: dict[int, str] = {}
auth_token: Optional[str] = None


async def login() -> str:
    """Cache a JWT for the lifetime of the bot."""
    global auth_token
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{GENIE_API}/api/auth/login",
            json={"email": GENIE_EMAIL, "password": GENIE_PASSWORD},
        )
        r.raise_for_status()
        auth_token = r.json()["access_token"]
        log.info("Logged in to Genie API")
        return auth_token


async def chat_with_genie(message: str, session_id: Optional[str]) -> dict:
    if auth_token is None:
        await login()
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{GENIE_API}/api/genie/chat",
            headers=headers,
            json={"message": message, "session_id": session_id},
        )
        if r.status_code in (401, 403):
            await login()
            headers = {"Authorization": f"Bearer {auth_token}"}
            r = await client.post(
                f"{GENIE_API}/api/genie/chat",
                headers=headers,
                json={"message": message, "session_id": session_id},
            )
        r.raise_for_status()
        return r.json()


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (id={bot.user.id})")


@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot or msg.author == bot.user:
        return
    if not isinstance(msg.channel, discord.DMChannel):
        return  # only DMs
    if ALLOWED_USERS and msg.author.id not in ALLOWED_USERS:
        await msg.channel.send("🪔 Sorry, this Genie only answers to its Boss.")
        return

    async with msg.channel.typing():
        try:
            session_id = session_per_user.get(msg.author.id)
            data = await chat_with_genie(msg.content, session_id)
            session_per_user[msg.author.id] = data["session_id"]
            reply = data.get("reply") or "…"
            # Discord max 2000 chars per message
            for i in range(0, len(reply), 1900):
                await msg.channel.send(reply[i : i + 1900])
        except Exception as exc:
            log.exception("chat failed")
            await msg.channel.send(f"⚠️ Genie tripped: `{exc}`")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
