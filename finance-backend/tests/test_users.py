from tests.conftest import auth_headers, login_user, make_admin, register_user


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass"), admin_id


def test_get_user_by_id(client):
    token, admin_id = _admin_token(client)
    resp = client.get(f"/users/{admin_id}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == admin_id


def test_get_nonexistent_user(client):
    token, _ = _admin_token(client)
    resp = client.get("/users/9999", headers=auth_headers(token))
    assert resp.status_code == 404


def test_admin_cannot_deactivate_self(client):
    token, admin_id = _admin_token(client)
    resp = client.patch(f"/users/{admin_id}/status", json={"is_active": False}, headers=auth_headers(token))
    assert resp.status_code == 400


def test_admin_can_deactivate_other_user(client):
    token, _ = _admin_token(client)
    register_user(client, "target", "targetpass")
    users = client.get("/users", headers=auth_headers(token)).json()
    target_id = next(u["id"] for u in users if u["username"] == "target")
    resp = client.patch(f"/users/{target_id}/status", json={"is_active": False}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_deactivated_user_cannot_login(client):
    token, _ = _admin_token(client)
    register_user(client, "target", "targetpass")
    users = client.get("/users", headers=auth_headers(token)).json()
    target_id = next(u["id"] for u in users if u["username"] == "target")
    client.patch(f"/users/{target_id}/status", json={"is_active": False}, headers=auth_headers(token))
    resp = client.post("/auth/login", json={"username": "target", "password": "targetpass"})
    assert resp.status_code == 401
