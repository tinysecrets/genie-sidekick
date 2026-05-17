"""
agents/tools/registry.py
========================
Tool registry + dispatcher used by the ReAct loop in agents/_loop.py.

Every tool is a callable taking a single `args: dict` and returning a string.
No paid services. No auth required by default. Tools that hit the network
(web.search, web.fetch) use free public endpoints.
"""
from __future__ import annotations

import inspect
import json
import shlex
import subprocess
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict


ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------

def fs_read(args: dict) -> str:
    p = Path(args["path"]).expanduser().resolve()
    if not p.exists():
        return f"ERROR: not found: {p}"
    return p.read_text(errors="replace")


def fs_write(args: dict) -> str:
    p = Path(args["path"]).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args["content"])
    return f"wrote {len(args['content'])} bytes to {p}"


def fs_list(args: dict) -> str:
    p = Path(args.get("path", ".")).expanduser().resolve()
    if not p.is_dir():
        return f"ERROR: not a directory: {p}"
    return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()))


def fs_glob(args: dict) -> str:
    base = Path(args.get("base", ".")).expanduser().resolve()
    return "\n".join(sorted(str(x.relative_to(base)) for x in base.glob(args["pattern"])))


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

def sh_run(args: dict) -> str:
    cmd = args["cmd"]
    cwd = args.get("cwd", str(ROOT))
    timeout = int(args.get("timeout", 60))
    try:
        proc = subprocess.run(
            cmd if isinstance(cmd, list) else shlex.split(cmd),
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return json.dumps({
            "exit": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        })
    except subprocess.TimeoutExpired:
        return f"ERROR: timeout after {timeout}s"
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Python exec (in a subprocess; respects the sovereign user — no sandbox here)
# ---------------------------------------------------------------------------

def py_exec(args: dict) -> str:
    code = args["code"]
    timeout = int(args.get("timeout", 30))
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout, cwd=str(ROOT),
        )
        return json.dumps({
            "exit": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        })
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Web — free DuckDuckGo HTML search + plain urllib fetch
# ---------------------------------------------------------------------------

class _DDGParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_a = False
        self._cur_href = ""
        self._cur_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            if "result__a" in (d.get("class") or ""):
                self._in_a = True
                self._cur_href = d.get("href", "")
                self._cur_text = []

    def handle_endtag(self, tag):
        if tag == "a" and self._in_a:
            self._in_a = False
            self.results.append({
                "title": "".join(self._cur_text).strip(),
                "url": self._cur_href,
            })

    def handle_data(self, data):
        if self._in_a:
            self._cur_text.append(data)


def web_search(args: dict) -> str:
    q = args["query"]
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
    req = urllib.request.Request(url, headers={"User-Agent": "sovereign-team/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"
    p = _DDGParser()
    p.feed(html)
    top = p.results[:10]
    return json.dumps(top, indent=2) if top else "(no results)"


def web_fetch(args: dict) -> str:
    url = args["url"]
    req = urllib.request.Request(url, headers={"User-Agent": "sovereign-team/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read(2_000_000).decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"
    # Crude HTML strip
    import re as _re
    text = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", body)
    text = _re.sub(r"<[^>]+>", " ", text)
    text = _re.sub(r"\s+", " ", text).strip()
    return text[:8000]


# ---------------------------------------------------------------------------
# Task delegation — recursive spawn of a sibling agent
# ---------------------------------------------------------------------------

def task_spawn(args: dict) -> str:
    """Delegate a sub-task to another role. Avoids deep recursion via a counter."""
    role = args["role"]
    order = args["order"]
    # Late import to avoid circular dep
    from agents._loop import run_with_tools  # noqa: WPS433
    return run_with_tools(role, order, max_steps=int(args.get("max_steps", 6)))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TOOLS: Dict[str, Callable[[dict], str]] = {
    "fs.read": fs_read,
    "fs.write": fs_write,
    "fs.list": fs_list,
    "fs.glob": fs_glob,
    "sh.run": sh_run,
    "py.exec": py_exec,
    "web.search": web_search,
    "web.fetch": web_fetch,
    "task.spawn": task_spawn,
}

TOOL_SCHEMAS: Dict[str, str] = {
    "fs.read":    '{"path": "<file>"}',
    "fs.write":   '{"path": "<file>", "content": "<text>"}',
    "fs.list":    '{"path": "<dir, optional>"}',
    "fs.glob":    '{"pattern": "**/*.py", "base": "<dir, optional>"}',
    "sh.run":     '{"cmd": "<shell string>", "cwd": "<dir, optional>", "timeout": 60}',
    "py.exec":    '{"code": "<python>", "timeout": 30}',
    "web.search": '{"query": "<text>"}',
    "web.fetch":  '{"url": "<https url>"}',
    "task.spawn": '{"role": "research|design|coding|qa|reporting|integration", "order": "<text>"}',
}


def describe_tools() -> str:
    lines = ["You may call exactly one tool per turn using JSON. Available tools:"]
    for name, schema in TOOL_SCHEMAS.items():
        lines.append(f"  - {name}  args={schema}")
    return "\n".join(lines)


def invoke(tool: str, args: dict) -> str:
    fn = TOOLS.get(tool)
    if not fn:
        return f"ERROR: unknown tool {tool!r}"
    try:
        sig = inspect.signature(fn)
        if "args" not in sig.parameters:
            return f"ERROR: bad tool signature for {tool}"
        return fn(args or {})
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {type(e).__name__}: {e}"
