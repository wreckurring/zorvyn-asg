from tests.conftest import auth_headers, login_user, make_admin, register_user


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_categories_empty(client):
    token = _admin_token(client)
    resp = client.get("/dashboard/categories", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_categories_returns_distinct(client):
    token = _admin_token(client)
    for _ in range(3):
        client.post("/transactions", json={"amount": 100.0, "type": "income", "category": "Salary", "date": "2024-01-01"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 200.0, "type": "expense", "category": "Rent", "date": "2024-01-05"}, headers=auth_headers(token))
    resp = client.get("/dashboard/categories", headers=auth_headers(token))
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) == 2
    assert "Salary" in cats
    assert "Rent" in cats


def test_categories_filter_by_type(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 100.0, "type": "income", "category": "Salary", "date": "2024-01-01"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 200.0, "type": "expense", "category": "Rent", "date": "2024-01-05"}, headers=auth_headers(token))
    resp = client.get("/dashboard/categories?type=income", headers=auth_headers(token))
    cats = resp.json()
    assert cats == ["Salary"]


def test_by_category_with_date_filter(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 1000.0, "type": "income", "category": "Jan", "date": "2024-01-15"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 2000.0, "type": "income", "category": "Jun", "date": "2024-06-15"}, headers=auth_headers(token))
    resp = client.get("/dashboard/by-category?date_from=2024-06-01&date_to=2024-06-30", headers=auth_headers(token))
    assert resp.status_code == 200
    cats = [r["category"] for r in resp.json()]
    assert "Jun" in cats
    assert "Jan" not in cats
