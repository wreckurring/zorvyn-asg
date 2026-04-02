from tests.conftest import auth_headers, login_user, make_admin, register_user

BASE_TXN = {
    "amount": 1200.0,
    "type": "income",
    "category": "Consulting",
    "date": "2024-04-15",
}


def _admin_client(client):
    register_user(client, "admin", "adminpass")
    token = login_user(client, "admin", "adminpass")
    admin_id = client.get("/users", headers=auth_headers(token)).json()[0]["id"]
    make_admin(client, token, admin_id)
    return login_user(client, "admin", "adminpass")


def test_create_transaction(client):
    token = _admin_client(client)
    resp = client.post("/transactions", json=BASE_TXN, headers=auth_headers(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 1200.0
    assert data["category"] == "Consulting"
    assert data["is_deleted"] is False


def test_list_transactions(client):
    token = _admin_client(client)
    client.post("/transactions", json=BASE_TXN, headers=auth_headers(token))
    resp = client.get("/transactions", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["results"]) == 1


def test_filter_by_type(client):
    token = _admin_client(client)
    client.post("/transactions", json=BASE_TXN, headers=auth_headers(token))
    client.post("/transactions", json={**BASE_TXN, "type": "expense", "category": "Rent"}, headers=auth_headers(token))
    resp = client.get("/transactions?type=income", headers=auth_headers(token))
    assert all(t["type"] == "income" for t in resp.json()["results"])


def test_filter_by_category(client):
    token = _admin_client(client)
    client.post("/transactions", json=BASE_TXN, headers=auth_headers(token))
    client.post("/transactions", json={**BASE_TXN, "category": "Groceries"}, headers=auth_headers(token))
    resp = client.get("/transactions?category=Consulting", headers=auth_headers(token))
    assert all("Consulting" in t["category"] for t in resp.json()["results"])


def test_update_transaction(client):
    token = _admin_client(client)
    txn = client.post("/transactions", json=BASE_TXN, headers=auth_headers(token)).json()
    resp = client.put(f"/transactions/{txn['id']}", json={"amount": 2500.0}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["amount"] == 2500.0


def test_soft_delete_hides_transaction(client):
    token = _admin_client(client)
    txn = client.post("/transactions", json=BASE_TXN, headers=auth_headers(token)).json()
    client.delete(f"/transactions/{txn['id']}", headers=auth_headers(token))
    resp = client.get("/transactions", headers=auth_headers(token))
    assert resp.json()["total"] == 0


def test_update_nonexistent_transaction(client):
    token = _admin_client(client)
    resp = client.put("/transactions/9999", json={"amount": 100.0}, headers=auth_headers(token))
    assert resp.status_code == 404


def test_negative_amount_rejected(client):
    token = _admin_client(client)
    resp = client.post("/transactions", json={**BASE_TXN, "amount": -50.0}, headers=auth_headers(token))
    assert resp.status_code == 422


def test_pagination(client):
    token = _admin_client(client)
    for i in range(5):
        client.post("/transactions", json={**BASE_TXN, "category": f"Cat{i}"}, headers=auth_headers(token))
    resp = client.get("/transactions?limit=2&skip=0", headers=auth_headers(token))
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["total"] == 5


def test_get_single_transaction(client):
    token = _admin_client(client)
    txn = client.post("/transactions", json=BASE_TXN, headers=auth_headers(token)).json()
    resp = client.get(f"/transactions/{txn['id']}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == txn["id"]


def test_get_single_transaction_not_found(client):
    token = _admin_client(client)
    resp = client.get("/transactions/9999", headers=auth_headers(token))
    assert resp.status_code == 404


def test_invalid_date_range_rejected(client):
    token = _admin_client(client)
    resp = client.get("/transactions?date_from=2024-06-01&date_to=2024-01-01", headers=auth_headers(token))
    assert resp.status_code == 400


def test_validation_error_format(client):
    token = _admin_client(client)
    resp = client.post("/transactions", json={"amount": -10, "type": "invalid"}, headers=auth_headers(token))
    assert resp.status_code == 422
    body = resp.json()
    assert "errors" in body
    assert "detail" in body
