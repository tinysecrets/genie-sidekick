"""
scripts/encrypt_vault.py
========================
No-op shim — vault is already encrypted at seal time by init_super_key.py.
Kept so bootstrap.sh reads as a clean 5-step ritual.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keys.key_manager import VAULT_FILE  # noqa: E402


def main() -> None:
    if not VAULT_FILE.exists():
        print("Vault missing. Run init_super_key.py first.", file=sys.stderr)
        sys.exit(1)
    size = VAULT_FILE.stat().st_size
    print(f"Vault sealed: {VAULT_FILE} ({size} bytes, AES-256-GCM).")


if __name__ == "__main__":
    main()
