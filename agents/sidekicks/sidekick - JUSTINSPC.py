"""
agents/sidekicks/sidekick.py
============================
Generic Genie Sidekick runner (L3 Agent Key).

Sidekicks are stateless, single-purpose helpers spawned by a specialist agent.
This module exposes a thin wrapper around the LLM client; specialise via prompt.

Usage (called by an agent):
    from agents.sidekicks.sidekick import spawn
    out = spawn("coding:scaffolder", "create a Python package skeleton named foo")
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agents._llm import chat  # noqa: E402


SIDEKICK_PROMPTS = {
    "reporting:notifier":  "Turn the report into a 280-char status ping. No emojis.",
    "reporting:digest":    "Roll up multi-day reports into a single 5-bullet brief.",
    "design:moodboard":    "Describe (do not generate) 6 reference images with style notes.",
    "design:palette":      "Output a 5-stop hex palette with WCAG contrast notes.",
    "coding:scaffolder":   "Output a folder tree + empty file list. No code.",
    "coding:refactor":     "Propose a narrow refactor as a unified diff sketch.",
    "qa:a11y":             "List a11y violations as P0/P1/P2 with WCAG references.",
    "qa:perf":             "List perf issues as P0/P1/P2 with metric thresholds.",
}


def spawn(sidekick_id: str, order: str, vault_env: dict | None = None) -> str:
    extra = SIDEKICK_PROMPTS.get(sidekick_id, "You are a Genie Sidekick.")
    user = f"{extra}\n\nOrder:\n{order}"
    return chat("sidekick", user, vault_env=vault_env).text


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("sidekick_id")
    p.add_argument("order", nargs="+")
    a = p.parse_args()
    print(spawn(a.sidekick_id, " ".join(a.order)))
