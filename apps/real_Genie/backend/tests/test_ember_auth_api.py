"""End-to-end backend tests for Ember API (auth-gated version).

Uses seeded test sessions (per /app/auth_testing.md). Two users verify isolation.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    fe = "/app/frontend/.env"
    if os.path.exists(fe):
        for line in open(fe):
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = (BASE_URL or "").rstrip("/")
API = f"{BASE_URL}/api"

TOKEN_A = os.environ.get("TOKEN_A")
TOKEN_B = os.environ.get("TOKEN_B")


def _auth(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def s_a():
    s = requests.Session()
    s.headers.update(_auth(TOKEN_A))
    return s


@pytest.fixture(scope="session")
def s_b():
    s = requests.Session()
    s.headers.update(_auth(TOKEN_B))
    return s


@pytest.fixture(scope="session")
def s_anon():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Auth gating (401 without auth) ---
class TestAuthGating:
    def test_me_no_auth(self, s_anon):
        assert s_anon.get(f"{API}/auth/me").status_code == 401

    def test_session_invalid(self, s_anon):
        r = s_anon.post(f"{API}/auth/session", json={"session_id": "invalid_xxx"})
        assert r.status_code == 401

    @pytest.mark.parametrize("method,path,body", [
        ("GET", "/conversations", None),
        ("POST", "/conversations", {}),
        ("POST", "/chat", {"message": "hi"}),
        ("GET", "/memory", None),
        ("POST", "/memory", {"content": "x"}),
        ("PATCH", "/memory/abc", {"content": "x"}),
        ("DELETE", "/memory/abc", None),
        ("GET", "/settings/persona", None),
        ("PUT", "/settings/persona", {"persona": "x"}),
    ])
    def test_all_endpoints_require_auth(self, s_anon, method, path, body):
        r = s_anon.request(method, f"{API}{path}", json=body)
        assert r.status_code == 401, f"{method} {path} => {r.status_code}"


# --- /api/auth/me with Bearer ---
class TestAuthMe:
    def test_me_ok(self, s_a):
        r = s_a.get(f"{API}/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert "user_id" in d and "email" in d and d["name"] == "Ember Tester A"


# --- Conversations & Chat ---
class TestConversationsAndChat:
    def test_create_conversation(self, s_a):
        r = s_a.post(f"{API}/conversations")
        assert r.status_code == 200
        c = r.json()
        assert "id" in c
        TestConversationsAndChat.cid = c["id"]

    def test_list_conversations(self, s_a):
        r = s_a.get(f"{API}/conversations")
        assert r.status_code == 200
        assert any(x["id"] == TestConversationsAndChat.cid for x in r.json())

    def test_chat_real_claude(self, s_a):
        r = s_a.post(f"{API}/chat", json={
            "conversation_id": TestConversationsAndChat.cid,
            "message": "Say the word 'ember' back to me in one short sentence."
        }, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["assistant_message"]["role"] == "assistant"
        assert len(d["assistant_message"]["content"]) > 0
        TestConversationsAndChat.cid = d["conversation_id"]

    def test_messages_persisted(self, s_a):
        r = s_a.get(f"{API}/conversations/{TestConversationsAndChat.cid}/messages")
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_rename(self, s_a):
        r = s_a.patch(f"{API}/conversations/{TestConversationsAndChat.cid}",
                      json={"title": "TEST_renamed"})
        assert r.status_code == 200
        assert r.json()["title"] == "TEST_renamed"

    def test_delete_clears_messages(self, s_a):
        cid = TestConversationsAndChat.cid
        r = s_a.delete(f"{API}/conversations/{cid}")
        assert r.status_code == 200
        # messages should also be gone: GET returns 404 for the conv
        r2 = s_a.get(f"{API}/conversations/{cid}/messages")
        assert r2.status_code == 404


# --- Memory CRUD ---
class TestMemory:
    def test_crud(self, s_a):
        r = s_a.post(f"{API}/memory", json={"content": "TEST_likes oat milk"})
        assert r.status_code == 200
        mid = r.json()["id"]

        r = s_a.get(f"{API}/memory")
        assert r.status_code == 200
        assert any(m["id"] == mid for m in r.json())

        r = s_a.patch(f"{API}/memory/{mid}", json={"content": "TEST_likes almond milk"})
        assert r.status_code == 200 and r.json()["content"] == "TEST_likes almond milk"

        r = s_a.delete(f"{API}/memory/{mid}")
        assert r.status_code == 200


# --- Persona ---
class TestPersona:
    def test_get_default(self, s_a):
        r = s_a.get(f"{API}/settings/persona")
        assert r.status_code == 200
        d = r.json()
        assert "persona" in d and "default" in d

    def test_update_and_get(self, s_a):
        r = s_a.put(f"{API}/settings/persona", json={"persona": "TEST_sassy and direct"})
        assert r.status_code == 200 and r.json()["persona"] == "TEST_sassy and direct"
        r2 = s_a.get(f"{API}/settings/persona")
        assert r2.json()["persona"] == "TEST_sassy and direct"

    def test_empty_resets_to_default(self, s_a):
        r = s_a.put(f"{API}/settings/persona", json={"persona": "   "})
        assert r.status_code == 200
        default = s_a.get(f"{API}/settings/persona").json()["default"]
        assert r.json()["persona"] == default

    def test_too_long(self, s_a):
        r = s_a.put(f"{API}/settings/persona", json={"persona": "x" * 1001})
        assert r.status_code == 400


# --- Data isolation ---
class TestIsolation:
    def test_separate_data(self, s_a, s_b):
        # A creates a memory + conversation
        ma = s_a.post(f"{API}/memory", json={"content": "TEST_ISO_A_secret"}).json()
        ca = s_a.post(f"{API}/conversations").json()

        # B should not see them
        mems_b = s_b.get(f"{API}/memory").json()
        assert not any(m["id"] == ma["id"] for m in mems_b)
        convs_b = s_b.get(f"{API}/conversations").json()
        assert not any(c["id"] == ca["id"] for c in convs_b)

        # B cannot rename/delete A's conv (404)
        assert s_b.patch(f"{API}/conversations/{ca['id']}", json={"title": "hijack"}).status_code == 404
        assert s_b.delete(f"{API}/conversations/{ca['id']}").status_code == 404
        assert s_b.delete(f"{API}/memory/{ma['id']}").status_code == 404

        # cleanup by A
        s_a.delete(f"{API}/memory/{ma['id']}")
        s_a.delete(f"{API}/conversations/{ca['id']}")


# --- Auto memory extraction ---
class TestAutoExtraction:
    def test_grows_after_chat(self, s_a):
        before = {m["content"] for m in s_a.get(f"{API}/memory").json()}
        r = s_a.post(f"{API}/chat", json={
            "message": "Quick note: my name is TestNovaXZ and I work as a nurse in Lisbon."
        }, timeout=120)
        assert r.status_code == 200
        cid = r.json()["conversation_id"]
        new = []
        for _ in range(8):
            time.sleep(2)
            after = s_a.get(f"{API}/memory").json()
            diff = [m for m in after if m["content"] not in before]
            if diff:
                new = diff
                break
        for m in new:
            s_a.delete(f"{API}/memory/{m['id']}")
        s_a.delete(f"{API}/conversations/{cid}")
        assert new, "No memory extracted within ~16s"


# --- Logout ---
class TestLogout:
    def test_logout_invalidates(self):
        # Use fresh seeded session so TOKEN_A stays usable for earlier fixture order
        # We'll seed on-the-fly via a dedicated token: re-use TOKEN_B is risky if tests share.
        # Instead, just verify logout on TOKEN_A at the very end.
        s = requests.Session()
        s.headers.update(_auth(TOKEN_A))
        r = s.post(f"{API}/auth/logout")
        assert r.status_code == 200
        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 401
