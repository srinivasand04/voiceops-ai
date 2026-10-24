import uuid

from fastapi.testclient import TestClient

from app.auth import hash_password, verify_password
from app.main import app


client = TestClient(app)


def _register():
    email = f"user-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse-1"}
    )

    return email, response


def test_password_hash_round_trip():
    stored = hash_password("s3cret-pass")

    assert stored != "s3cret-pass"
    assert verify_password("s3cret-pass", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("anything", "not-a-valid-hash")


def test_register_login_and_me():
    email, response = _register()

    assert response.status_code == 201
    assert response.json()["user"]["email"] == email

    login = client.post(
        "/api/auth/login", json={"email": email, "password": "correct-horse-1"}
    )
    assert login.status_code == 200

    token = login.json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["email"] == email


def test_wrong_password_rejected():
    email, _ = _register()

    response = client.post(
        "/api/auth/login", json={"email": email, "password": "not-the-password"}
    )

    assert response.status_code == 401


def test_duplicate_email_rejected():
    email, _ = _register()

    response = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse-1"}
    )

    assert response.status_code == 409


def test_calls_require_login():
    assert client.get("/api/calls").status_code == 401
    assert client.get("/api/stats").status_code == 401
    assert client.post("/api/calls/1/process").status_code == 401
    assert client.get("/api/calls", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_non_admin_cannot_delete_all_calls():
    _register()  # guarantees at least one user already exists
    _, second = _register()
    token = second.json()["token"]

    assert second.json()["user"]["role"] == "analyst"

    response = client.delete("/api/calls", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_logged_in_user_can_list_calls_and_stats():
    _, response = _register()
    headers = {"Authorization": f"Bearer {response.json()['token']}"}

    assert client.get("/api/calls", headers=headers).status_code == 200

    stats = client.get("/api/stats", headers=headers)
    assert stats.status_code == 200
    assert "total_calls" in stats.json()
