from tests.conftest import auth_headers, login_user, make_admin, register_user


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_create_budget(client):
    token = _admin_token(client)
    resp = client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token))
    assert resp.status_code == 201
    assert resp.json()["category"] == "Rent"
    assert resp.json()["monthly_limit"] == 3500.0


def test_duplicate_budget_rejected(client):
    token = _admin_token(client)
    client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token))
    resp = client.post("/budgets", json={"category": "Rent", "monthly_limit": 4000.0, "month": "2024-01"}, headers=auth_headers(token))
    assert resp.status_code == 409


def test_list_budgets_by_month(client):
    token = _admin_token(client)
    client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token))
    client.post("/budgets", json={"category": "Food", "monthly_limit": 1000.0, "month": "2024-02"}, headers=auth_headers(token))
    resp = client.get("/budgets?month=2024-01", headers=auth_headers(token))
    assert len(resp.json()) == 1
    assert resp.json()[0]["month"] == "2024-01"


def test_update_budget(client):
    token = _admin_token(client)
    b = client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token)).json()
    resp = client.patch(f"/budgets/{b['id']}?monthly_limit=4000.0", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["monthly_limit"] == 4000.0


def test_delete_budget(client):
    token = _admin_token(client)
    b = client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token)).json()
    resp = client.delete(f"/budgets/{b['id']}", headers=auth_headers(token))
    assert resp.status_code == 204


def test_budget_status_under(client):
    token = _admin_token(client)
    client.post("/budgets", json={"category": "Rent", "monthly_limit": 3500.0, "month": "2024-01"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 2800.0, "type": "expense", "category": "Rent", "date": "2024-01-05"}, headers=auth_headers(token))
    resp = client.get("/dashboard/budget-status?month=2024-01", headers=auth_headers(token))
    row = next(r for r in resp.json() if r["category"] == "Rent")
    assert row["status"] == "under_budget"
    assert row["actual"] == 2800.0
    assert row["variance"] == 700.0


def test_budget_status_over(client):
    token = _admin_token(client)
    client.post("/budgets", json={"category": "Rent", "monthly_limit": 2000.0, "month": "2024-01"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 3200.0, "type": "expense", "category": "Rent", "date": "2024-01-05"}, headers=auth_headers(token))
    resp = client.get("/dashboard/budget-status?month=2024-01", headers=auth_headers(token))
    row = next(r for r in resp.json() if r["category"] == "Rent")
    assert row["status"] == "over_budget"
    assert row["utilization_pct"] == 160.0


def test_budget_status_no_budget(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 500.0, "type": "expense", "category": "Groceries", "date": "2024-01-10"}, headers=auth_headers(token))
    resp = client.get("/dashboard/budget-status?month=2024-01", headers=auth_headers(token))
    row = next((r for r in resp.json() if r["category"] == "Groceries"), None)
    assert row is not None
    assert row["status"] == "no_budget"
