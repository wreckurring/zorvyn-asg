from tests.conftest import auth_headers, login_user, make_admin, register_user

TRANSACTION_PAYLOAD = {
    "amount": 500.0,
    "type": "income",
    "category": "Salary",
    "date": "2024-03-01",
}


def _setup_admin(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    token = login_user(client, "admin", "adminpass")
    return token


def test_viewer_cannot_create_transaction(client):
    register_user(client, "viewer", "viewerpass")
    token = login_user(client, "viewer", "viewerpass")
    resp = client.post("/transactions", json=TRANSACTION_PAYLOAD, headers=auth_headers(token))
    assert resp.status_code == 403


def test_analyst_can_create_transaction(client):
    admin_token = _setup_admin(client)
    register_user(client, "analyst", "analystpass")
    analyst = client.get("/users", headers=auth_headers(admin_token)).json()
    analyst_id = next(u["id"] for u in analyst if u["username"] == "analyst")
    client.patch(f"/users/{analyst_id}/role", json={"role": "analyst"}, headers=auth_headers(admin_token))
    analyst_token = login_user(client, "analyst", "analystpass")
    resp = client.post("/transactions", json=TRANSACTION_PAYLOAD, headers=auth_headers(analyst_token))
    assert resp.status_code == 201


def test_analyst_cannot_update_transaction(client):
    admin_token = _setup_admin(client)
    txn = client.post("/transactions", json=TRANSACTION_PAYLOAD, headers=auth_headers(admin_token)).json()

    register_user(client, "analyst", "analystpass")
    analyst = client.get("/users", headers=auth_headers(admin_token)).json()
    analyst_id = next(u["id"] for u in analyst if u["username"] == "analyst")
    client.patch(f"/users/{analyst_id}/role", json={"role": "analyst"}, headers=auth_headers(admin_token))
    analyst_token = login_user(client, "analyst", "analystpass")

    resp = client.put(f"/transactions/{txn['id']}", json={"amount": 999.0}, headers=auth_headers(analyst_token))
    assert resp.status_code == 403


def test_admin_can_delete_transaction(client):
    admin_token = _setup_admin(client)
    txn = client.post("/transactions", json=TRANSACTION_PAYLOAD, headers=auth_headers(admin_token)).json()
    resp = client.delete(f"/transactions/{txn['id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 204


def test_viewer_cannot_manage_users(client):
    register_user(client, "viewer", "viewerpass")
    token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/users", headers=auth_headers(token))
    assert resp.status_code == 403


def test_non_admin_cannot_change_roles(client):
    register_user(client, "viewer", "viewerpass")
    token = login_user(client, "viewer", "viewerpass")
    resp = client.patch("/users/1/role", json={"role": "admin"}, headers=auth_headers(token))
    assert resp.status_code == 403
