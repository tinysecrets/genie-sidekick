"""
Local Genie interface for the agent team.

Run:
    SUPER_KEY='your-passphrase' python3 scripts/ui_server.py
Then open:
    http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "docs" / "ui_runs"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


@dataclass
class Job:
    id: str
    goal: str
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    lines: list[str] = field(default_factory=list)
    exit_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "lines": self.lines,
            "exit_code": self.exit_code,
        }


JOBS: dict[str, Job] = {}
JOBS_LOCK = threading.Lock()


def _json_response(handler: BaseHTTPRequestHandler, code: int, data: dict) -> None:
    body = json.dumps(data).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(
    handler: BaseHTTPRequestHandler,
    code: int,
    body: str,
    content_type: str = "text/html; charset=utf-8",
) -> None:
    raw = body.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def _ollama_health() -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {"ok": False, "host": host, "error": str(exc)}
    models = [item.get("name", "") for item in data.get("models", [])]
    return {"ok": True, "host": host, "models": models}


def _append(job: Job, line: str) -> None:
    with JOBS_LOCK:
        job.lines.append(line.rstrip())


def _save_transcript(job: Job) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{job.id}.md"
    content = "\n".join(job.lines).strip() + "\n"
    path.write_text(content, encoding="utf-8")


def _run_job(job: Job, super_key: str, max_steps: int) -> None:
    env = os.environ.copy()
    env["SUPER_KEY"] = super_key
    env.setdefault("GENIE_DETERMINISTIC_CRITIC", "1")
    env.setdefault("AGENT_MAX_STEPS", str(max_steps))
    env.setdefault("OLLAMA_NUM_PREDICT", "80")
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [
        sys.executable,
        str(ROOT / "agents" / "genie" / "genie.py"),
        "--serial",
        job.goal,
    ]
    job.status = "running"
    _append(job, "Welcome. You do not have to be sudo to birth your dreams.")
    _append(job, "The team is gathering around your idea now.")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            _append(job, line)
        job.exit_code = proc.wait()
        job.status = "passed" if job.exit_code == 0 else "failed"
    except Exception as exc:  # noqa: BLE001
        job.exit_code = 1
        job.status = "failed"
        _append(job, f"ERROR: {type(exc).__name__}: {exc}")
    finally:
        job.finished_at = time.time()
        _save_transcript(job)


def _start_job(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    idea = str(payload.get("idea", "")).strip()
    opinion = str(payload.get("opinion", "")).strip()
    super_key = str(payload.get("super_key") or os.environ.get("SUPER_KEY", ""))
    max_steps = int(payload.get("max_steps") or os.environ.get("AGENT_MAX_STEPS", 1))

    if not idea:
        return 400, {"error": "Tell the team what you want to build first."}
    if not super_key:
        return 400, {"error": "Set SUPER_KEY or enter it for this local run."}

    goal = idea
    if opinion:
        goal += "\n\nUser preference and personal opinion:\n" + opinion

    job = Job(id=uuid.uuid4().hex[:12], goal=goal)
    with JOBS_LOCK:
        JOBS[job.id] = job

    thread = threading.Thread(
        target=_run_job,
        args=(job, super_key, max_steps),
        daemon=True,
    )
    thread.start()
    return 202, {"job": job.to_dict()}


class Handler(BaseHTTPRequestHandler):
    server_version = "GenieUI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            _text_response(self, 200, HTML)
            return
        if self.path == "/api/health":
            _json_response(
                self,
                200,
                {
                    "vault": (ROOT / "keys" / "vault" / "keys.enc").exists(),
                    "ollama": _ollama_health(),
                },
            )
            return
        if self.path.startswith("/api/jobs/"):
            job_id = self.path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                _json_response(self, 404, {"error": "job not found"})
                return
            _json_response(self, 200, {"job": job.to_dict()})
            return
        _text_response(self, 404, "Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/build":
            _json_response(self, 404, {"error": "not found"})
            return
        try:
            code, data = _start_job(_read_json(self))
        except json.JSONDecodeError:
            code, data = 400, {"error": "Invalid JSON body."}
        _json_response(self, code, data)


def main() -> None:
    host = os.environ.get("DREAM_UI_HOST", DEFAULT_HOST)
    port = int(os.environ.get("DREAM_UI_PORT", DEFAULT_PORT))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Genie is awake at http://{host}:{port}", flush=True)
    print("Press Ctrl-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGenie is resting.", flush=True)
    finally:
        server.server_close()


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Genie</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17201d;
      --muted: #5e6b65;
      --paper: #f8f7f2;
      --line: #d9ded4;
      --leaf: #27715f;
      --blue: #315f8f;
      --gold: #9a6b20;
      --rose: #9b4f5f;
      --white: #ffffff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 16px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
    }
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }
    header {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 24px;
      align-items: end;
      min-height: 210px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 22px;
    }
    h1 {
      margin: 0;
      font-size: clamp(40px, 7vw, 84px);
      line-height: 0.95;
      letter-spacing: 0;
    }
    .lede {
      margin: 18px 0 0;
      max-width: 680px;
      color: var(--muted);
      font-size: 19px;
    }
    .status {
      display: grid;
      gap: 10px;
      padding: 16px;
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--gold);
      display: inline-block;
      margin-right: 8px;
    }
    section {
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 24px;
      margin-top: 24px;
    }
    form, .panel {
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    label {
      display: block;
      font-weight: 700;
      margin: 0 0 8px;
    }
    textarea, input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      color: var(--ink);
      background: #fbfbf8;
      resize: vertical;
      font: inherit;
    }
    textarea { min-height: 150px; }
    .short { min-height: 88px; }
    .field { margin-bottom: 16px; }
    button {
      width: 100%;
      border: 0;
      border-radius: 6px;
      padding: 13px 16px;
      background: var(--leaf);
      color: white;
      font-weight: 800;
      cursor: pointer;
      font: inherit;
    }
    button:disabled {
      opacity: 0.58;
      cursor: wait;
    }
    .roles {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin: 14px 0;
    }
    .role {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px;
      color: var(--muted);
      background: #fbfbf8;
      font-size: 14px;
    }
    .role.active {
      border-color: var(--blue);
      color: var(--blue);
      font-weight: 800;
    }
    .role.done {
      border-color: var(--leaf);
      color: var(--leaf);
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 520px;
      overflow: auto;
      padding: 14px;
      background: #111816;
      color: #e8f0eb;
      border-radius: 8px;
      font-size: 13px;
    }
    .note {
      border-left: 4px solid var(--rose);
      padding-left: 12px;
      color: var(--muted);
      min-height: 48px;
    }
    .small {
      color: var(--muted);
      font-size: 13px;
    }
    @media (max-width: 820px) {
      header, section { grid-template-columns: 1fr; }
      .roles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Genie</h1>
        <p class="lede">
          You do not have to be sudo to birth your dreams. Tell Genie what
          you want, add your opinion, and stay close while the team builds.
        </p>
      </div>
      <div class="status">
        <div>
          <span class="dot" id="dot"></span>
          <strong id="health">Checking</strong>
        </div>
        <div class="small" id="health-detail">
          Looking for the vault and model backend.
        </div>
      </div>
    </header>

    <section>
      <form id="build-form">
        <div class="field">
          <label for="idea">What are we building?</label>
          <textarea id="idea" required
            placeholder="A booking app for local stylists with profiles,
payments, and client reminders."></textarea>
        </div>
        <div class="field">
          <label for="opinion">Your personal opinion</label>
          <textarea id="opinion" class="short"
            placeholder="What matters most to you? Style, users, speed,
privacy, money, community..."></textarea>
        </div>
        <div class="field" id="key-field">
          <label for="super-key">Super Key for this local run</label>
          <input id="super-key" type="password" autocomplete="current-password"
            placeholder="Leave blank when SUPER_KEY is set in the server shell">
        </div>
        <button id="go" type="submit">Ask Genie</button>
        <p class="small">
          Runs locally through Genie using the configured free local model path.
        </p>
      </form>

      <div class="panel">
        <h2>Genie Room</h2>
        <div class="roles" id="roles"></div>
        <p class="note" id="note">Genie is waiting for your first dream.</p>
        <pre id="log"></pre>
      </div>
    </section>
  </main>

  <script>
    const roleNames = ["research", "design", "code", "qa", "report", "integration"];
    const roles = document.getElementById("roles");
    const log = document.getElementById("log");
    const note = document.getElementById("note");
    const form = document.getElementById("build-form");
    const button = document.getElementById("go");
    let activeJob = null;

    function renderRoles(lines) {
      const text = lines.join("\n").toLowerCase();
      roles.innerHTML = "";
      for (const role of roleNames) {
        const el = document.createElement("div");
        el.className = "role";
        el.textContent = role;
        const marker = "--> [" + role + "]";
        if (text.includes(marker)) el.classList.add("done");
        const last = lines.slice(-8).join("\n").toLowerCase();
        if (last.includes(marker)) el.classList.add("active");
        roles.appendChild(el);
      }
    }

    function buildNote(job) {
      const lines = job.lines || [];
      const text = lines.join("\n");
      if (text.includes("VERDICT: PASS")) {
        return "The team completed the run and the gate passed.";
      }
      if (text.includes("VERDICT: FAIL")) {
        return "The team completed the run and found something to revisit.";
      }
      for (const role of roleNames) {
        if (text.toLowerCase().includes("--> [" + role + "]")) {
          return "Now tending the " + role + " part of the build.";
        }
      }
      if (job.status === "running") {
        return "Genie is listening and shaping the plan.";
      }
      return "Genie is waiting for your first dream.";
    }

    async function refreshHealth() {
      const res = await fetch("/api/health");
      const data = await res.json();
      const health = document.getElementById("health");
      const detail = document.getElementById("health-detail");
      const dot = document.getElementById("dot");
      if (data.vault && data.ollama.ok) {
        health.textContent = "Ready";
        detail.textContent = "Vault found. Models: " + data.ollama.models.join(", ");
        dot.style.background = "var(--leaf)";
      } else {
        health.textContent = "Needs setup";
        detail.textContent = data.ollama.error || "Run bootstrap and start Ollama.";
        dot.style.background = "var(--gold)";
      }
    }

    async function poll() {
      if (!activeJob) return;
      const res = await fetch("/api/jobs/" + activeJob);
      const data = await res.json();
      const job = data.job;
      log.textContent = (job.lines || []).join("\n");
      renderRoles(job.lines || []);
      note.textContent = buildNote(job);
      log.scrollTop = log.scrollHeight;
      if (job.status === "running" || job.status === "queued") {
        setTimeout(poll, 1800);
      } else {
        button.disabled = false;
      button.textContent = "Ask Genie";
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      button.disabled = true;
      button.textContent = "Genie Is Listening";
      note.textContent = "Genie is opening the room.";
      log.textContent = "";
      renderRoles([]);
      const payload = {
        idea: document.getElementById("idea").value,
        opinion: document.getElementById("opinion").value,
        super_key: document.getElementById("super-key").value,
      };
      const res = await fetch("/api/build", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        note.textContent = data.error || "The team could not start.";
        button.disabled = false;
        button.textContent = "Ask Genie";
        return;
      }
      activeJob = data.job.id;
      poll();
    });

    renderRoles([]);
    refreshHealth();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
