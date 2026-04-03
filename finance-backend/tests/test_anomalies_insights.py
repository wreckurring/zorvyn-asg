from tests.conftest import auth_headers, login_user, make_admin, register_user


def _admin_token(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def _post_txn(client, token, amount, category="Salary", txn_type="income", txn_date="2024-01-10"):
    client.post(
        "/transactions",
        json={"amount": amount, "type": txn_type, "category": category, "date": txn_date},
        headers=auth_headers(token),
    )


def test_anomalies_empty_when_insufficient_data(client):
    token = _admin_token(client)
    _post_txn(client, token, 100.0)
    _post_txn(client, token, 110.0)
    resp = client.get("/dashboard/anomalies", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_anomalies_detects_outlier(client):
    token = _admin_token(client)
    for amount in [100.0, 105.0, 95.0, 102.0, 98.0]:
        _post_txn(client, token, amount)
    _post_txn(client, token, 500.0)
    resp = client.get("/dashboard/anomalies", headers=auth_headers(token))
    assert resp.status_code == 200
    anomalies = resp.json()
    assert len(anomalies) >= 1
    assert anomalies[0]["amount"] == 500.0
    assert anomalies[0]["z_score"] > 2.0


def test_anomalies_sorted_by_z_score(client):
    token = _admin_token(client)
    for amount in [100.0, 105.0, 95.0, 102.0, 98.0]:
        _post_txn(client, token, amount)
    _post_txn(client, token, 500.0)
    _post_txn(client, token, 800.0)
    resp = client.get("/dashboard/anomalies", headers=auth_headers(token))
    scores = [a["z_score"] for a in resp.json()]
    assert scores == sorted(scores, reverse=True)


def test_anomalies_custom_threshold(client):
    token = _admin_token(client)
    for amount in [100.0, 105.0, 95.0, 102.0, 98.0]:
        _post_txn(client, token, amount)
    _post_txn(client, token, 200.0)
    resp_strict = client.get("/dashboard/anomalies?z_threshold=3.0", headers=auth_headers(token))
    resp_loose = client.get("/dashboard/anomalies?z_threshold=1.0", headers=auth_headers(token))
    assert len(resp_loose.json()) >= len(resp_strict.json())


def test_insights_structure(client):
    token = _admin_token(client)
    _post_txn(client, token, 5000.0, category="Salary", txn_type="income")
    _post_txn(client, token, 1200.0, category="Rent", txn_type="expense")
    resp = client.get("/dashboard/insights", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "savings_rate_pct" in body
    assert "top_expense_category" in body
    assert "avg_daily_expense" in body
    assert "total_transactions" in body
    assert body["total_transactions"] == 2


def test_insights_savings_rate(client):
    token = _admin_token(client)
    _post_txn(client, token, 10000.0, txn_type="income")
    _post_txn(client, token, 4000.0, txn_type="expense", category="Expenses")
    resp = client.get("/dashboard/insights", headers=auth_headers(token))
    assert resp.json()["savings_rate_pct"] == 60.0


def test_insights_viewer_allowed(client):
    token = _admin_token(client)
    _post_txn(client, token, 1000.0, txn_type="income")
    register_user(client, "viewer", "viewerpass")
    viewer_token = login_user(client, "viewer", "viewerpass")
    resp = client.get("/dashboard/insights", headers=auth_headers(viewer_token))
    assert resp.status_code == 200
