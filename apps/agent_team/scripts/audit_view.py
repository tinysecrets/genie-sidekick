"""
scripts/audit_view.py
=====================
Decrypt and print the entire append-only audit log.
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keys.key_manager import audit_read  # noqa: E402


def main() -> None:
    pw = os.environ.get("SUPER_KEY") or getpass.getpass("Super Key: ")
    for entry in audit_read(pw):
        print(entry)


if __name__ == "__main__":
    main()
