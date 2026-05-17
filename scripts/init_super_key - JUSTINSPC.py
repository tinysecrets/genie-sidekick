"""
scripts/init_super_key.py
=========================
Initialize (or re-confirm) the Level-0 Super Key.

The passphrase itself is NEVER stored. Only:
  - a random 16-byte salt (keys/vault/salt.bin)
  - the encrypted vault produced after derivation (keys/vault/keys.enc)
"""
from __future__ import annotations

import argparse
import getpass
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keys.key_manager import (  # noqa: E402
    derive_all,
    seal_vault,
    super_key_to_vault_key,
    write_salt,
    SALT_FILE,  # noqa: F401  (re-exported for downstream tools)
    VAULT_FILE,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-env", action="store_true",
                        help="Read passphrase from SUPER_KEY env var (CI mode).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing vault if present.")
    args = parser.parse_args()

    if VAULT_FILE.exists() and not args.force:
        print("Vault already initialized at:", VAULT_FILE)
        print("Use --force to overwrite. Aborting.")
        return

    if args.from_env:
        pw = os.environ.get("SUPER_KEY", "")
        if not pw:
            print("SUPER_KEY env var is empty.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Choose your Super Key passphrase. It will NEVER be stored.")
        print("If you lose it, the vault becomes unrecoverable.\n")
        pw = getpass.getpass("Super Key passphrase: ")
        pw2 = getpass.getpass("Confirm passphrase:   ")
        if pw != pw2:
            print("Passphrases do not match.", file=sys.stderr)
            sys.exit(1)
        if len(pw) < 12:
            print("Passphrase must be at least 12 characters.", file=sys.stderr)
            sys.exit(1)

    salt = secrets.token_bytes(16)
    write_salt(salt)
    vault_key = super_key_to_vault_key(pw, salt)

    # Use the (passphrase-derived) vault_key itself as the seed for L1 derivation;
    # this means every keyset is deterministically tied to the human passphrase.
    bundle = derive_all(vault_key)
    seal_vault(bundle, vault_key)

    print(f"Super Key sealed. Vault: {VAULT_FILE}")
    print(f"Run ID: {bundle.run_id}")


if __name__ == "__main__":
    main()
