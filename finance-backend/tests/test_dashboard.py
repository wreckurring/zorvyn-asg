from tests.conftest import auth_headers, login_user, make_admin, register_user

INCOME = {"amount": 3000.0, "type": "income", "category": "Salary", "date": "2024-01-10"}
EXPENSE = {"amount": 800.0, "type": "expense", "category": "Rent", "date": "2024-01-15"}


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_summary(client):
    token = _admin_token(client)
    client.post("/transactions", json=INCOME, headers=auth_headers(token))
    client.post("/transactions", json=EXPENSE, headers=auth_headers(token))
    resp = client.get("/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == 3000.0
    assert data["total_expenses"] == 800.0
    assert data["net_balance"] == 2200.0


def test_summary_empty(client):
    token = _admin_token(client)
    resp = client.get("/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["net_balance"] == 0.0


def test_by_category(client):
    token = _admin_token(client)
    client.post("/transactions", json=INCOME, headers=auth_headers(token))
    client.post("/transactions", json=EXPENSE, headers=auth_headers(token))
    resp = client.get("/dashboard/by-category", headers=auth_headers(token))
    assert resp.status_code == 200
    categories = [r["category"] for r in resp.json()]
    assert "Salary" in categories
    assert "Rent" in categories


def test_trends(client):
    token = _admin_token(client)
    client.post("/transactions", json=INCOME, headers=auth_headers(token))
    resp = client.get("/dashboard/trends", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert "month" in resp.json()[0]


def test_recent(client):
    token = _admin_token(client)
    for i in range(3):
        client.post("/transactions", json={**INCOME, "category": f"Cat{i}"}, headers=auth_headers(token))
    resp = client.get("/dashboard/recent?limit=2", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_viewer_can_access_dashboard(client):
    token = _admin_token(client)
    client.post("/transactions", json=INCOME, headers=auth_headers(token))

    register_user(client, "viewer", "viewerpass")
    viewer_token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/dashboard/summary", headers=auth_headers(viewer_token))
    assert resp.status_code == 200
