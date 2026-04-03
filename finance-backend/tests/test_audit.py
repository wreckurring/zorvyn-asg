from tests.conftest import auth_headers, login_user, make_admin, register_user

TXN = {"amount": 750.0, "type": "income", "category": "Freelance", "date": "2024-03-01"}


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_create_generates_audit_log(client):
    token = _admin_token(client)
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    resp = client.get("/audit-logs", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["results"][0]["action"] == "create"
    assert body["results"][0]["resource_type"] == "transaction"


def test_update_generates_audit_log(client):
    token = _admin_token(client)
    txn = client.post("/transactions", json=TXN, headers=auth_headers(token)).json()
    client.put(f"/transactions/{txn['id']}", json={"amount": 999.0}, headers=auth_headers(token))
    resp = client.get("/audit-logs", headers=auth_headers(token))
    actions = [r["action"] for r in resp.json()["results"]]
    assert "update" in actions


def test_delete_generates_audit_log(client):
    token = _admin_token(client)
    txn = client.post("/transactions", json=TXN, headers=auth_headers(token)).json()
    client.delete(f"/transactions/{txn['id']}", headers=auth_headers(token))
    resp = client.get("/audit-logs", headers=auth_headers(token))
    actions = [r["action"] for r in resp.json()["results"]]
    assert "delete" in actions


def test_audit_log_filter_by_resource_type(client):
    token = _admin_token(client)
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    resp = client.get("/audit-logs?resource_type=transaction", headers=auth_headers(token))
    assert all(r["resource_type"] == "transaction" for r in resp.json()["results"])


def test_audit_log_filter_by_user(client):
    token = _admin_token(client)
    users = client.get("/users", headers=auth_headers(token)).json()
    admin_id = users[0]["id"]
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    resp = client.get(f"/audit-logs?user_id={admin_id}", headers=auth_headers(token))
    assert all(r["user_id"] == admin_id for r in resp.json()["results"])


def test_non_admin_cannot_access_audit_logs(client):
    register_user(client, "viewer", "viewerpass")
    token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/audit-logs", headers=auth_headers(token))
    assert resp.status_code == 403


def test_audit_log_pagination(client):
    token = _admin_token(client)
    for i in range(5):
        client.post("/transactions", json={**TXN, "category": f"Cat{i}"}, headers=auth_headers(token))
    resp = client.get("/audit-logs?limit=2", headers=auth_headers(token))
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["total"] == 5
