"""
keys/key_manager.py
====================
Hierarchical key derivation, vault sealing, and revocation for the Sovereign Team.

Topology:
    L0 Super Key       (human passphrase, never stored)
       └─ L1 Master Key (HKDF, info="master")
            ├─ L2 Pseudo Keys per role (HKDF, info=f"pseudo:{role}")
            │     └─ L3 Agent Keys per sidekick (HKDF, info=f"agent:{role}:{sidekick}")
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = REPO_ROOT / "keys" / "vault"
VAULT_FILE = VAULT_DIR / "keys.enc"
SALT_FILE = VAULT_DIR / "salt.bin"
META_FILE = VAULT_DIR / "meta.json"

PBKDF2_ITERATIONS = 480_000
KEY_LEN = 32  # 256 bits


# ---------------------------------------------------------------------------
# Low-level primitives
# ---------------------------------------------------------------------------

def _hkdf(material: bytes, info: bytes, salt: bytes = b"sovereign-team") -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        info=info,
    ).derive(material)


def super_key_to_vault_key(passphrase: str, salt: bytes) -> bytes:
    """Stretch the human passphrase into a 256-bit vault encryption key."""
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    ).derive(passphrase.encode("utf-8"))


# ---------------------------------------------------------------------------
# Key hierarchy
# ---------------------------------------------------------------------------

ROLES = ("reporting", "design", "coding", "qa", "research", "integration")
SIDEKICKS_PER_ROLE: Dict[str, tuple] = {
    "reporting": ("notifier", "digest"),
    "design": ("moodboard", "palette"),
    "coding": ("scaffolder", "refactor"),
    "qa": ("a11y", "perf"),
    "research": ("scout", "synthesist"),
    "integration": ("sdk", "wirer"),
}


@dataclass
class KeyBundle:
    master: str  # b64
    pseudo: Dict[str, str]
    agent: Dict[str, str]
    run_id: str

    def to_dict(self) -> dict:
        return asdict(self)


def derive_all(super_key_material: bytes, run_id: Optional[str] = None) -> KeyBundle:
    """Derive Master, Pseudo, and Agent keys from raw Super Key material."""
    run_id = run_id or secrets.token_hex(8)
    master = _hkdf(super_key_material, info=f"master:{run_id}".encode())

    pseudo: Dict[str, bytes] = {}
    agent: Dict[str, bytes] = {}
    for role in ROLES:
        p = _hkdf(master, info=f"pseudo:{role}".encode())
        pseudo[role] = p
        for sk in SIDEKICKS_PER_ROLE.get(role, ()):
            agent[f"{role}:{sk}"] = _hkdf(p, info=f"agent:{role}:{sk}".encode())

    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return KeyBundle(
        master=b64(master),
        pseudo={k: b64(v) for k, v in pseudo.items()},
        agent={k: b64(v) for k, v in agent.items()},
        run_id=run_id,
    )


# ---------------------------------------------------------------------------
# Vault I/O
# ---------------------------------------------------------------------------

def seal_vault(bundle: KeyBundle, vault_key: bytes) -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    nonce = secrets.token_bytes(12)
    aes = AESGCM(vault_key)
    plaintext = json.dumps(bundle.to_dict()).encode("utf-8")
    ct = aes.encrypt(nonce, plaintext, associated_data=b"sovereign-vault-v1")
    VAULT_FILE.write_bytes(nonce + ct)
    META_FILE.write_text(json.dumps({"version": 1, "run_id": bundle.run_id}, indent=2))
    try:
        os.chmod(VAULT_FILE, 0o600)
    except Exception:
        pass


def open_vault(vault_key: bytes) -> KeyBundle:
    if not VAULT_FILE.exists():
        raise FileNotFoundError("Vault not initialized. Run bootstrap.sh first.")
    blob = VAULT_FILE.read_bytes()
    nonce, ct = blob[:12], blob[12:]
    aes = AESGCM(vault_key)
    plaintext = aes.decrypt(nonce, ct, associated_data=b"sovereign-vault-v1")
    data = json.loads(plaintext.decode("utf-8"))
    return KeyBundle(**data)


def load_salt() -> bytes:
    if not SALT_FILE.exists():
        raise FileNotFoundError("Salt file missing. Run bootstrap.sh first.")
    return SALT_FILE.read_bytes()


def write_salt(salt: bytes) -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    SALT_FILE.write_bytes(salt)


# ---------------------------------------------------------------------------
# Public helpers used by agents
# ---------------------------------------------------------------------------

def unlock(passphrase: str) -> KeyBundle:
    """Open the vault using the Super Key passphrase."""
    salt = load_salt()
    vault_key = super_key_to_vault_key(passphrase, salt)
    return open_vault(vault_key)


def rotate(level: str, passphrase: str) -> KeyBundle:
    """Rotate keys at the given level: 'master' | 'pseudo' | 'agent' | 'all'."""
    salt = load_salt()
    vault_key = super_key_to_vault_key(passphrase, salt)
    old = open_vault(vault_key)
    # New material: random for the rotated level, keep run_id stable upstream of it.
    if level in ("all", "master"):
        new_master = secrets.token_bytes(KEY_LEN)
        bundle = derive_all(new_master, run_id=secrets.token_hex(8))
    elif level == "pseudo":
        master = base64.b64decode(old.master)
        new = derive_all(master, run_id=secrets.token_hex(8))
        bundle = new
    elif level == "agent":
        # Re-derive only agent keys from existing pseudo keys
        agent: Dict[str, str] = {}
        for role in ROLES:
            p = base64.b64decode(old.pseudo[role])
            for sk in SIDEKICKS_PER_ROLE.get(role, ()):
                agent[f"{role}:{sk}"] = base64.b64encode(
                    _hkdf(p, info=f"agent:{role}:{sk}:{secrets.token_hex(4)}".encode())
                ).decode("ascii")
        bundle = KeyBundle(master=old.master, pseudo=old.pseudo, agent=agent,
                           run_id=old.run_id)
    elif level == "all":
        new_master = secrets.token_bytes(KEY_LEN)
        bundle = derive_all(new_master, run_id=secrets.token_hex(8))
    else:
        raise ValueError(f"Unknown rotation level: {level}")

    seal_vault(bundle, vault_key)
    return bundle


# ---------------------------------------------------------------------------
# Encrypted append-only audit log
# ---------------------------------------------------------------------------

AUDIT_FILE = VAULT_DIR / "audit.log"


def audit_append(passphrase: str, entry: str) -> None:
    """Append-only AES-GCM audit entry. Each line is its own envelope."""
    import datetime
    salt = load_salt()
    vault_key = super_key_to_vault_key(passphrase, salt)
    nonce = secrets.token_bytes(12)
    aes = AESGCM(vault_key)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = f"{ts}  {entry}".encode("utf-8")
    blob = nonce + aes.encrypt(nonce, payload, associated_data=b"sovereign-audit-v1")
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open("ab") as f:
        f.write(base64.b64encode(blob) + b"\n")


def audit_read(passphrase: str) -> list[str]:
    """Decrypt the entire audit log into a list of lines (for diagnostics only)."""
    if not AUDIT_FILE.exists():
        return []
    salt = load_salt()
    vault_key = super_key_to_vault_key(passphrase, salt)
    aes = AESGCM(vault_key)
    out: list[str] = []
    for line in AUDIT_FILE.read_bytes().splitlines():
        if not line.strip():
            continue
        blob = base64.b64decode(line)
        nonce, ct = blob[:12], blob[12:]
        try:
            out.append(aes.decrypt(nonce, ct, associated_data=b"sovereign-audit-v1").decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            out.append(f"<undecryptable entry: {e}>")
    return out
