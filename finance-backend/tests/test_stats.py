from tests.conftest import auth_headers, login_user, make_admin, register_user


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_stats_empty(client):
    token = _admin_token(client)
    resp = client.get("/transactions/stats", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_stats_returns_aggregates(client):
    token = _admin_token(client)
    for amount in [100.0, 200.0, 300.0]:
        client.post(
            "/transactions",
            json={"amount": amount, "type": "income", "category": "Salary", "date": "2024-01-10"},
            headers=auth_headers(token),
        )
    resp = client.get("/transactions/stats", headers=auth_headers(token))
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["category"] == "Salary"
    assert row["count"] == 3
    assert row["total"] == 600.0
    assert row["avg"] == 200.0
    assert row["min"] == 100.0
    assert row["max"] == 300.0


def test_stats_filter_by_type(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 500.0, "type": "income", "category": "Salary", "date": "2024-01-10"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 200.0, "type": "expense", "category": "Rent", "date": "2024-01-10"}, headers=auth_headers(token))
    resp = client.get("/transactions/stats?type=expense", headers=auth_headers(token))
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "Rent"


def test_stats_filter_by_date(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 100.0, "type": "income", "category": "Jan", "date": "2024-01-10"}, headers=auth_headers(token))
    client.post("/transactions", json={"amount": 200.0, "type": "income", "category": "Jun", "date": "2024-06-10"}, headers=auth_headers(token))
    resp = client.get("/transactions/stats?date_from=2024-06-01&date_to=2024-06-30", headers=auth_headers(token))
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "Jun"


def test_stats_viewer_allowed(client):
    token = _admin_token(client)
    client.post("/transactions", json={"amount": 100.0, "type": "income", "category": "Salary", "date": "2024-01-10"}, headers=auth_headers(token))
    register_user(client, "viewer", "viewerpass")
    viewer_token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/transactions/stats", headers=auth_headers(viewer_token))
    assert resp.status_code == 200
