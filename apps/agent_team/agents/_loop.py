"""
agents/_loop.py
===============
Iterative ReAct-style tool-use loop. Any agent can run inside it.

Protocol (the model is asked to emit EXACTLY one JSON object per turn):
    {"thought": "...", "tool": "fs.write", "args": {...}}
or  {"thought": "...", "final": "..."}

The loop:
  - feeds the conversation to the model
  - parses the JSON action
  - executes the tool
  - appends the result and loops
  - terminates on a "final" action or when max_steps is reached
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Tuple

from agents._llm import chat
from agents.tools import describe_tools, invoke


JSON_RE = re.compile(r"\{[\s\S]*\}")


def _extract_json(text: str) -> dict | None:
    """Best-effort JSON extraction from a model response."""
    # Try fenced ```json ... ``` first
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:  # noqa: BLE001
            pass
    # Then the largest brace span
    m = JSON_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None


def _format_transcript(transcript: List[Tuple[str, str]]) -> str:
    return "\n".join(f"[{who}] {what}" for who, what in transcript[-12:])


def run_with_tools(role: str, goal: str, vault_env: dict | None = None,
                   max_steps: int = 10) -> str:
    """Run an agent with tool access until it emits `final` or hits max_steps."""
    max_steps = int(os.environ.get("AGENT_MAX_STEPS", str(max_steps)))
    transcript: list[tuple[str, str]] = [("user", goal)]
    tools_doc = describe_tools()
    invalid_json_count = 0

    for step in range(max_steps):
        user_msg = (
            f"{tools_doc}\n\n"
            "Reply with EXACTLY ONE JSON object, no prose around it. Either:\n"
            '  {"thought": "...", "tool": "<name>", "args": {...}}'
            "  to call a tool, or\n"
            '  {"thought": "...", "final": "<answer>"}              to finish.\n\n'
            f"Conversation so far:\n{_format_transcript(transcript)}\n\n"
            f"Step {step + 1}/{max_steps}. What is your next action?"
        )
        resp = chat(role, user_msg, vault_env=vault_env).text
        action = _extract_json(resp)
        if not action:
            invalid_json_count += 1
            if invalid_json_count >= 2:
                return (
                    "The model did not emit a tool JSON action after retry. "
                    f"Latest answer:\n{resp}"
                )
            transcript.append(("assistant", resp))
            transcript.append(
                ("system", "ERROR: no valid JSON action found; respond again.")
            )
            continue

        transcript.append(("assistant", json.dumps(action)))
        invalid_json_count = 0

        if "final" in action:
            return action["final"]

        tool_name = action.get("tool")
        args = action.get("args") or {}
        if not tool_name:
            transcript.append(("system", "ERROR: missing 'tool' key."))
            continue

        result = invoke(tool_name, args)
        transcript.append(("tool", f"{tool_name} -> {result[:1500]}"))

    # Soft-fall: ask the agent to summarise what it has so far
    summary = chat(
        role,
        "You hit the step budget. Summarise the result for the human in "
        "6 lines max.\n\n"
        f"Transcript:\n{_format_transcript(transcript)}",
        vault_env=vault_env,
    ).text
    return summary
