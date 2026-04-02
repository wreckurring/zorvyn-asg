from tests.conftest import auth_headers, login_user, make_admin, register_user

TXN = {"amount": 500.0, "type": "income", "category": "Salary", "date": "2024-01-10"}


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_export_returns_csv(client):
    token = _admin_token(client)
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    resp = client.get("/transactions/export", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().split("\n")
    assert lines[0].startswith("id,date,type")
    assert len(lines) == 2


def test_export_empty(client):
    token = _admin_token(client)
    resp = client.get("/transactions/export", headers=auth_headers(token))
    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert len(lines) == 1


def test_export_filter_by_type(client):
    token = _admin_token(client)
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    client.post("/transactions", json={**TXN, "type": "expense", "category": "Rent"}, headers=auth_headers(token))
    resp = client.get("/transactions/export?type=expense", headers=auth_headers(token))
    lines = resp.text.strip().split("\n")
    assert len(lines) == 2
    assert "expense" in lines[1]


def test_export_viewer_allowed(client):
    token = _admin_token(client)
    client.post("/transactions", json=TXN, headers=auth_headers(token))
    register_user(client, "viewer", "viewerpass")
    viewer_token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/transactions/export", headers=auth_headers(viewer_token))
    assert resp.status_code == 200
