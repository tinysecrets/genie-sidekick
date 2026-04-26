# Genie Discord Bot Bridge

DM your Genie from anywhere via Discord — phone, watch, browser. Whatever has Discord installed.

## Setup (5 min)

### 1. Create a Discord bot
https://discord.com/developers/applications → **New Application** → name it "Genie".
- Left sidebar → **Bot** → **Reset Token** → copy somewhere safe.
- Same page → toggle ON **"MESSAGE CONTENT INTENT"** (mandatory for DMs).

### 2. Invite the bot to a server (or just DM it)
- **OAuth2 → URL Generator** → scopes: `bot`
- Bot permissions: `Send Messages`, `Read Message History`
- Copy the generated URL → open in browser → add to a personal server.
  *(Or skip the server step — bots can be DM'd directly once they're "live" via the token.)*

### 3. Find YOUR Discord User ID
Discord settings → Advanced → enable **Developer Mode**. Then right-click your username in any chat → **Copy User ID**.

### 4. Configure
Copy `.env.example` to `.env`:
```
DISCORD_BOT_TOKEN=...           # from step 1
GENIE_API_URL=https://genie.wah-lah.com
GENIE_ADMIN_EMAIL=you@example.com
GENIE_ADMIN_PASSWORD=...
ALLOWED_DISCORD_USER_IDS=123456789012345678  # YOUR ID from step 3
```

### 5. Run
```bash
pip install -r requirements.txt
python discord_bot.py
```

DM the bot. Genie answers. Each user gets their own session that persists across messages.

## Deploy 24/7 (optional)

Deploy this as a tiny Fly.io app:
```bash
flyctl launch --no-deploy
flyctl secrets set DISCORD_BOT_TOKEN=... GENIE_API_URL=... GENIE_ADMIN_EMAIL=... GENIE_ADMIN_PASSWORD=... ALLOWED_DISCORD_USER_IDS=...
flyctl deploy
```

Or run on a Raspberry Pi / spare laptop / always-on machine. ~80MB RAM idle.
