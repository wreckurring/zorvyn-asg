from tests.conftest import login_user, register_user


def _login_full(client, username, password):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    return resp.json()


def test_login_returns_both_tokens(client):
    register_user(client, "alice", "password1")
    body = _login_full(client, "alice", "password1")
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_refresh_returns_new_tokens(client):
    register_user(client, "alice", "password1")
    body = _login_full(client, "alice", "password1")
    resp = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert resp.status_code == 200
    new_body = resp.json()
    assert "access_token" in new_body
    assert "refresh_token" in new_body


def test_refresh_new_access_token_works(client):
    register_user(client, "alice", "password1")
    body = _login_full(client, "alice", "password1")
    new_body = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]}).json()
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {new_body['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_refresh_with_invalid_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401


def test_access_token_cannot_be_used_as_refresh(client):
    register_user(client, "alice", "password1")
    body = _login_full(client, "alice", "password1")
    resp = client.post("/auth/refresh", json={"refresh_token": body["access_token"]})
    assert resp.status_code == 401


def test_logout(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
