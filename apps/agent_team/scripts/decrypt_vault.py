"""
scripts/decrypt_vault.py
========================
Print the decrypted vault contents to stdout (Super Key passphrase required).
For diagnostics / migration only — never log this output anywhere durable.
"""
from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keys.key_manager import unlock  # noqa: E402


def main() -> None:
    pw = os.environ.get("SUPER_KEY") or getpass.getpass("Super Key passphrase: ")
    bundle = unlock(pw)
    print(json.dumps(bundle.to_dict(), indent=2))


if __name__ == "__main__":
    main()
