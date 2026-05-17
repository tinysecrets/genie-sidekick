"""
scripts/derive_keys.py
======================
Re-derive Master / Pseudo / Agent keys from the Super Key, or rotate a tier.

Usage:
    python scripts/derive_keys.py --all
    python scripts/derive_keys.py --rotate master
    python scripts/derive_keys.py --rotate pseudo
    python scripts/derive_keys.py --rotate agent
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keys.key_manager import rotate, unlock, VAULT_FILE  # noqa: E402


def _read_passphrase() -> str:
    pw = os.environ.get("SUPER_KEY")
    return pw if pw else getpass.getpass("Super Key passphrase: ")


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true",
                   help="Verify derivation (no rotation).")
    g.add_argument("--rotate", choices=["master", "pseudo", "agent", "all"],
                   help="Rotate the named tier.")
    args = p.parse_args()

    if not VAULT_FILE.exists():
        print("Vault not initialized. Run bootstrap.sh first.", file=sys.stderr)
        sys.exit(1)

    pw = _read_passphrase()

    if args.all:
        b = unlock(pw)
        print(f"OK — run_id={b.run_id}")
        print(f"  master: {b.master[:10]}...")
        for role, k in b.pseudo.items():
            print(f"  pseudo[{role}]: {k[:10]}...")
        for tag, k in b.agent.items():
            print(f"  agent[{tag}]: {k[:10]}...")
    else:
        b = rotate(args.rotate, pw)
        print(f"Rotated tier '{args.rotate}'. New run_id={b.run_id}")


if __name__ == "__main__":
    main()
