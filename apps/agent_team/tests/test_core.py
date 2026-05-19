"""Unit tests for the key hierarchy and tool registry. Run: `pytest -q`."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_full_key_lifecycle(tmp_path, monkeypatch):
    # Redirect vault to a temp dir
    import keys.key_manager as km
    monkeypatch.setattr(km, "VAULT_DIR", tmp_path)
    monkeypatch.setattr(km, "VAULT_FILE", tmp_path / "keys.enc")
    monkeypatch.setattr(km, "SALT_FILE", tmp_path / "salt.bin")
    monkeypatch.setattr(km, "META_FILE", tmp_path / "meta.json")
    monkeypatch.setattr(km, "AUDIT_FILE", tmp_path / "audit.log")

    import secrets
    salt = secrets.token_bytes(16)
    km.write_salt(salt)
    pw = "test-passphrase-1234567890"
    vault_key = km.super_key_to_vault_key(pw, salt)
    bundle = km.derive_all(vault_key)
    km.seal_vault(bundle, vault_key)

    # round-trip
    re_opened = km.unlock(pw)
    assert re_opened.master == bundle.master
    assert set(re_opened.pseudo.keys()) == set(km.ROLES)
    for role in km.ROLES:
        for sk in km.SIDEKICKS_PER_ROLE.get(role, ()):
            assert f"{role}:{sk}" in re_opened.agent

    # rotate agent: master+pseudo stable, agent keys change
    rotated = km.rotate("agent", pw)
    assert rotated.master == bundle.master
    assert rotated.pseudo == bundle.pseudo
    assert any(rotated.agent[k] != bundle.agent[k] for k in bundle.agent)

    # audit log round-trip
    km.audit_append(pw, "first entry")
    km.audit_append(pw, "second entry")
    entries = km.audit_read(pw)
    assert len(entries) == 2
    assert "first entry" in entries[0]
    assert "second entry" in entries[1]


def test_vault_loader_tolerates_env_tokens(tmp_path, monkeypatch):
    import json
    import secrets

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    import keys.key_manager as km

    monkeypatch.setattr(km, "VAULT_DIR", tmp_path)
    monkeypatch.setattr(km, "VAULT_FILE", tmp_path / "keys.enc")
    monkeypatch.setattr(km, "SALT_FILE", tmp_path / "salt.bin")
    monkeypatch.setattr(km, "META_FILE", tmp_path / "meta.json")

    salt = secrets.token_bytes(16)
    km.write_salt(salt)
    pw = "test-passphrase-1234567890"
    vault_key = km.super_key_to_vault_key(pw, salt)
    bundle = km.derive_all(vault_key)

    raw = bundle.to_dict()
    raw["env"] = {"GEMINI_API_KEY": "secret"}
    nonce = secrets.token_bytes(12)
    encrypted = AESGCM(vault_key).encrypt(
        nonce,
        json.dumps(raw).encode("utf-8"),
        associated_data=b"sovereign-vault-v1",
    )
    km.VAULT_FILE.write_bytes(nonce + encrypted)

    opened = km.unlock(pw)
    assert opened.master == bundle.master


def test_tool_registry_basic(tmp_path):
    from agents.tools import invoke, TOOLS
    assert "fs.write" in TOOLS and "fs.read" in TOOLS

    target = tmp_path / "hello.txt"
    out = invoke("fs.write", {"path": str(target), "content": "hi"})
    assert "wrote" in out
    out = invoke("fs.read", {"path": str(target)})
    assert out == "hi"

    out = invoke("py.exec", {"code": "print(2+2)"})
    assert '"stdout": "4\\n"' in out or '"stdout": "4\\r\\n"' in out


def test_genie_plan_parser():
    from agents.genie import genie
    cases = {
        "[research] x":          ("research", "x"),
        "1. [design] y":         ("design", "y"),
        "  2) [code] z":         ("code", "z"),
        "- [qa] audit":          ("qa", "audit"),
        "* [integration] sdk":   ("integration", "sdk"),
        "[report] s":            ("report", "s"),
    }
    for line, expected in cases.items():
        m = genie.ORDER_RE.match(line)
        assert m, f"no match: {line!r}"
        assert (m.group(1).lower(), m.group(2)) == expected
    assert genie.ORDER_RE.match("[other] nope") is None
    assert genie.ORDER_RE.match("plain text") is None
