"""
agents/genie/genie.py
=====================
The supervisor. Hardened upgrade:
  * Decomposes a goal into typed orders ([research|design|code|qa|report|integration])
  * Dispatches independent orders in PARALLEL (ThreadPoolExecutor)
  * Runs a critic pass at the end (QA agent gates delivery)
  * Appends every dispatch to the encrypted audit log

Usage:
    python agents/genie/genie.py "build me a static landing page"
    python agents/genie/genie.py --dry-run "..."     # plan only
    python agents/genie/genie.py --serial "..."      # disable parallel dispatch
"""
from __future__ import annotations

import argparse
import getpass
import importlib
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents._llm import chat  # noqa: E402
from keys.key_manager import (  # noqa: E402
    VAULT_FILE,
    audit_append,
    unlock,
)

ORDER_RE = re.compile(
    r"^\s*(?:[-*\d]+[.)]?\s*)?\[(report|design|code|qa|research|integration)\]\s*(.+)$",
    re.IGNORECASE,
)

ROLE_MAP = {
    "report":      ("reporting",    "reporting_agent"),
    "design":      ("design",       "design_agent"),
    "code":        ("coding",       "coding_agent"),
    "qa":          ("qa",           "qa_agent"),
    "research":    ("research",     "research_agent"),
    "integration": ("integration",  "integration_agent"),
}


def _load_passphrase() -> str:
    return os.environ.get("SUPER_KEY") or getpass.getpass("Super Key: ")


def _dispatch(order_type: str, order_text: str, vault_env: dict) -> str:
    pkg, mod_name = ROLE_MAP[order_type.lower()]
    mod = importlib.import_module(f"agents.{pkg}.{mod_name}")
    return mod.run(order_text, vault_env=vault_env)


def _critic(goal: str, results: list[tuple[str, str, str]], vault_env: dict) -> str:
    """QA-style critic that judges whether the assembled output satisfies the goal."""
    body = "\n\n".join(f"## [{t}] {o}\n{r}" for t, o, r in results)
    prompt = (
        f"Original goal:\n{goal}\n\n"
        f"Assembled team output:\n{body}\n\n"
        "Emit:\n"
        "  VERDICT: PASS|FAIL\n"
        "  RATIONALE: one paragraph\n"
        "  P0_ISSUES: bullets (or 'none')\n"
    )
    return chat("qa", prompt, vault_env=vault_env).text


def run(goal: str, dry_run: bool = False, serial: bool = False) -> str:
    if not VAULT_FILE.exists():
        print("Vault not initialized. Run bootstrap.sh first.", file=sys.stderr)
        sys.exit(1)

    pw = _load_passphrase()
    unlock(pw)  # validates Super Key
    # Pull any cloud tokens stored in the vault (set via scripts/set_token.py)
    try:
        from keys.key_manager import VAULT_FILE as _VF, super_key_to_vault_key, load_salt
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import json as _json
        _vk = super_key_to_vault_key(pw, load_salt())
        _blob = _VF.read_bytes()
        _raw = AESGCM(_vk).decrypt(_blob[:12], _blob[12:], associated_data=b"sovereign-vault-v1")
        vault_env: dict = _json.loads(_raw).get("env", {})
    except Exception:
        vault_env = {}

    # 1) Plan
    plan_prompt = (
        f"Goal from the Super Key holder:\n{goal}\n\n"
        "Produce: (a) one-sentence acknowledgement, (b) a numbered plan whose lines "
        "are typed orders in the form [research], [design], [code], [qa], [report], "
        "or [integration]. Output ONLY the acknowledgement + numbered orders, nothing else."
    )
    plan = chat("genie", plan_prompt, vault_env=vault_env).text
    print("\n=== Genie plan ===")
    print(plan)
    audit_append(pw, f"PLAN goal={goal!r}\n{plan}")

    if dry_run:
        return plan

    orders: list[tuple[str, str]] = []
    for line in plan.splitlines():
        m = ORDER_RE.match(line)
        if m:
            orders.append((m.group(1).lower(), m.group(2).strip()))

    if not orders:
        print("(no typed orders parsed; nothing to dispatch)")
        return plan

    # 2) Dispatch — parallel by default; design→code→qa ordering preserved
    #    only if --serial is passed.
    results: list[tuple[str, str, str]] = []
    if serial:
        for ot, txt in orders:
            print(f"\n--> [{ot}] {txt}")
            try:
                out = _dispatch(ot, txt, vault_env)
            except Exception as e:  # noqa: BLE001
                out = f"(agent error: {e})"
            audit_append(pw, f"DISPATCH [{ot}] {txt!r}")
            results.append((ot, txt, out))
    else:
        with ThreadPoolExecutor(max_workers=min(6, len(orders))) as pool:
            futs = {pool.submit(_dispatch, ot, txt, vault_env): (ot, txt) for ot, txt in orders}
            for fut in futs:
                ot, txt = futs[fut]
                try:
                    out = fut.result()
                except Exception as e:  # noqa: BLE001
                    out = f"(agent error: {e})"
                audit_append(pw, f"DISPATCH [{ot}] {txt!r}")
                results.append((ot, txt, out))

    # 3) Critic pass
    verdict = _critic(goal, results, vault_env)
    audit_append(pw, f"CRITIC\n{verdict}")

    # 4) Assemble
    print("\n=== Final assembly ===")
    final = [f"## [{t}] {o}\n\n{r}\n" for t, o, r in results]
    final.append(f"## Critic verdict\n\n{verdict}\n")
    final_text = "\n".join(final)
    print(final_text)
    return final_text


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("goal", nargs="+", help="The goal in natural language.")
    p.add_argument("--dry-run", action="store_true", help="Plan only; do not dispatch.")
    p.add_argument("--serial", action="store_true", help="Disable parallel dispatch.")
    args = p.parse_args()
    run(" ".join(args.goal), dry_run=args.dry_run, serial=args.serial)


if __name__ == "__main__":
    main()
