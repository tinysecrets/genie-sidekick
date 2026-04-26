# Genie · Personal AI Sidekick

Your own uncensored, multi-LLM AI sidekick. Magical persona, conversation memory,
hot-swappable brains (Cerebras / Venice / Ollama), pluggable tools.

A minimal, opinionated, deploy-anywhere FastAPI + React app. No bloat.

```
genie-sidekick/
├── backend/    FastAPI · JWT auth · MongoDB history · OpenAI-compatible multi-provider LLM
└── frontend/   React + Vite chat UI · session sidebar · provider switcher
```

## Quick start (local dev)

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — at minimum set ADMIN_EMAIL, ADMIN_PASSWORD, JWT_SECRET, MONGO_URL
# and ONE of: CEREBRAS_API_KEY, VENICE_API_KEY, OLLAMA_BASE_URL
uvicorn server:app --reload --port 8000
```

You need a MongoDB instance. Easiest options:
- Local: `brew install mongodb-community && brew services start mongodb-community`
- Free cloud: [MongoDB Atlas M0](https://www.mongodb.com/atlas) free tier
- Docker: `docker run -d -p 27017:27017 --name genie-mongo mongo:7`

### 2. Frontend
```bash
cd frontend
npm install
cp .env.example .env
# edit .env — set VITE_BACKEND_URL=http://localhost:8000
npm run dev
```

Visit `http://localhost:5173`, log in with the admin email/password from your backend `.env`.

## Brains (LLM providers)

Genie picks the first enabled provider in this priority order: **Ollama → Venice → Cerebras**.
You can override per-message in the UI.

| Provider | Speed | Censorship | Cost | Setup |
|---|---|---|---|---|
| **Cerebras** | 🚀 fastest | mild | very cheap | API key from [cloud.cerebras.ai](https://cloud.cerebras.ai) |
| **Venice** | medium | none (uncensored by design) | $20/mo Pro | API key from [venice.ai/settings/api](https://venice.ai/settings/api) |
| **Ollama** | depends on your hardware | depends on model | free | Run `ollama serve` locally; expose via tunnel for remote |

Set whichever you want in `backend/.env`. Empty entries are skipped automatically.

## Adding tools

Tools let Genie call your code mid-conversation. Add one in `backend/server.py`:

```python
async def tool_get_weather(args):
    city = args.get("city", "").strip()
    # ... your code ...
    return {"city": city, "temp_f": 72, "summary": "sunny"}

TOOLS["get_weather"] = tool_get_weather
```

Update the system prompt's `TOOLS AVAILABLE` section so Genie knows it exists. Genie
emits `<<TOOL name=get_weather args={"city":"Miami"} />>` and you handle the rest.

## Deploy

- **Backend**: Render / Fly.io / Railway. Free tiers all work. Add `backend/.env` vars in their dashboard.
- **Frontend**: Vercel / Netlify / Cloudflare Pages. Set `VITE_BACKEND_URL` to your backend's public URL at build time.
- **Database**: MongoDB Atlas M0 (free, 512MB).

## Security notes

- Single-user app: only the `ADMIN_EMAIL` from `.env` can log in. No registration.
- JWTs expire after 12h. Re-login required after.
- All chat history is keyed by `user_id` in MongoDB. Wipe with `db.messages.drop()`.

## License

Private. Don't ship Genie's persona to third-party platforms without revising the
system prompt — it's deliberately uncensored for personal use.
