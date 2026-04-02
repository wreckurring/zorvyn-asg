from tests.conftest import auth_headers, login_user, register_user


def test_update_email(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.patch("/auth/me", json={"email": "new@alice.com"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@alice.com"


def test_update_password(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.patch(
        "/auth/me",
        json={"current_password": "password1", "new_password": "newpassword1"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    new_token = login_user(client, "alice", "newpassword1")
    assert new_token


def test_update_password_wrong_current(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.patch(
        "/auth/me",
        json={"current_password": "wrongpass", "new_password": "newpassword1"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 400


def test_update_password_missing_current(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.patch("/auth/me", json={"new_password": "newpassword1"}, headers=auth_headers(token))
    assert resp.status_code == 400


def test_update_email_already_taken(client):
    register_user(client, "alice", "password1", email="alice@test.com")
    register_user(client, "bob", "password1", email="bob@test.com")
    token = login_user(client, "alice", "password1")
    resp = client.patch("/auth/me", json={"email": "bob@test.com"}, headers=auth_headers(token))
    assert resp.status_code == 409


def test_update_new_password_too_short(client):
    register_user(client, "alice", "password1")
    token = login_user(client, "alice", "password1")
    resp = client.patch(
        "/auth/me",
        json={"current_password": "password1", "new_password": "short"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422
