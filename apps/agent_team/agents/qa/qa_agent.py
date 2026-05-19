"""agents/qa/qa_agent.py — QA / Testing Agent (Pseudo Key, L2)."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agents._loop import run_with_tools  # noqa: E402


def run(order: str, vault_env: dict | None = None) -> str:
    return run_with_tools("qa", order, vault_env=vault_env, max_steps=10)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("order", nargs="+")
    a = p.parse_args()
    print(run(" ".join(a.order)))
