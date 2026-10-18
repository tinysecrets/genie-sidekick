# Security Policy

Genie Sidekick is a single-user FastAPI/React app with JWT authentication, MongoDB conversation history, and optional external LLM providers. Protect `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `JWT_SECRET`, `MONGO_URL`, provider keys, cookies, and stored conversations. Keep `.env` files, production database exports, user history, and logs with prompts out of Git.

Bind development services to loopback by default. Do not expose the backend or frontend to the public internet unless authentication, TLS, CORS, rate limiting, and database access controls have been reviewed end-to-end. Use synthetic accounts and a disposable local database in tests; do not route tests to a hosted backend or use real provider credentials by default.

Review tool-call handlers, provider response parsing, Markdown/HTML rendering, and session/logout behavior for injection or information leaks. Report potential vulnerabilities privately to the repository owner and redact session tokens or chat content from reproduction steps.
