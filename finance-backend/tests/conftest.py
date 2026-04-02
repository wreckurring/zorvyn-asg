import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://finance_user:finance_pass@localhost:5432/finance_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
_base_url, _test_db_name = TEST_DATABASE_URL.rsplit("/", 1)
_admin_url = f"{_base_url}/postgres"

_admin_engine = create_engine(_admin_url, isolation_level="AUTOCOMMIT")
with _admin_engine.connect() as conn:
    exists = conn.execute(
        text(f"SELECT 1 FROM pg_database WHERE datname = '{_test_db_name}'")
    ).fetchone()
    if not exists:
        conn.execute(text(f"CREATE DATABASE {_test_db_name}"))
_admin_engine.dispose()

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS transactiontype CASCADE"))
        conn.commit()


@pytest.fixture(scope="function")
def client(setup_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_user(client, username, password, email=None):
    email = email or f"{username}@test.com"
    return client.post("/auth/register", json={"username": username, "email": email, "password": password})


def login_user(client, username, password):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_admin(client, admin_token, user_id):
    client.patch(f"/users/{user_id}/role", json={"role": "admin"}, headers=auth_headers(admin_token))
