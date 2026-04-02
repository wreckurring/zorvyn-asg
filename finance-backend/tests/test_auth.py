from tests.conftest import auth_headers, login_user, register_user


def test_register_success(client):
    resp = register_user(client, "alice", "securepass")
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["role"] == "viewer"
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    register_user(client, "alice", "securepass")
    resp = register_user(client, "alice", "anotherpass")
    assert resp.status_code == 409


def test_register_duplicate_email(client):
    register_user(client, "alice", "securepass", email="same@test.com")
    resp = register_user(client, "bob", "securepass", email="same@test.com")
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = register_user(client, "alice", "short")
    assert resp.status_code == 422


def test_login_success(client):
    register_user(client, "alice", "securepass")
    resp = client.post("/auth/login", json={"username": "alice", "password": "securepass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    register_user(client, "alice", "securepass")
    resp = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/auth/login", json={"username": "ghost", "password": "pass"})
    assert resp.status_code == 401


def test_protected_route_no_token(client):
    resp = client.get("/transactions")
    assert resp.status_code == 403


def test_protected_route_invalid_token(client):
    resp = client.get("/transactions", headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401
