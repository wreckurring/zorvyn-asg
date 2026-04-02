# Finance Dashboard API

A role-based finance dashboard backend built with **FastAPI**, **PostgreSQL**, and **JWT authentication**. Supports full transaction CRUD, analytics endpoints, and fine-grained access control across three user roles.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |

---

## Project Structure

```
finance-backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── user.py
│   │   └── transaction.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── transaction.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── transactions.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── transaction_service.py
│   │   └── dashboard_service.py
│   └── middleware/
│       └── access_control.py
├── alembic/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_rbac.py
│   ├── test_transactions.py
│   └── test_dashboard.py
├── docker-compose.yml
├── seed.py
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd finance-backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work with the Docker Compose setup):

```
DATABASE_URL=postgresql://finance_user:finance_pass@localhost:5432/finance_db
SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Start PostgreSQL

```bash
docker-compose up -d
```

### 4. Run migrations

```bash
python -m alembic upgrade head
```

### 5. Seed demo data (optional)

```bash
python seed.py
```

This creates three users and 15 transactions across 3 months:

| Role | Username | Password |
|---|---|---|
| admin | admin | Admin@1234 |
| analyst | analyst | Analyst@1234 |
| viewer | viewer | Viewer@1234 |

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT |

### Users (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users` | List all users |
| POST | `/users` | Create a user |
| PATCH | `/users/{id}/role` | Change a user's role |
| PATCH | `/users/{id}/status` | Activate or deactivate a user |

### Transactions

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/transactions` | List transactions (filterable) | All |
| POST | `/transactions` | Create a transaction | Analyst, Admin |
| PUT | `/transactions/{id}` | Update a transaction | Admin |
| DELETE | `/transactions/{id}` | Soft delete a transaction | Admin |

**Query filters for `GET /transactions`:**
- `type` — `income` or `expense`
- `category` — partial match
- `date_from` / `date_to` — ISO date range
- `skip` / `limit` — pagination

### Dashboard

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/dashboard/summary` | Total income, expenses, net balance | All |
| GET | `/dashboard/by-category` | Totals grouped by category | All |
| GET | `/dashboard/trends` | Monthly income vs expense breakdown | All |
| GET | `/dashboard/recent` | Last N transactions (`?limit=10`) | All |

---

## Access Control

| Action | Viewer | Analyst | Admin |
|---|---|---|---|
| View transactions | yes | yes | yes |
| View dashboard | yes | yes | yes |
| Create transaction | no | yes | yes |
| Update transaction | no | no | yes |
| Delete transaction | no | no | yes |
| Manage users | no | no | yes |

Role checks are enforced as FastAPI dependencies injected per route — not scattered `if` checks.

---

## Running Tests

Requires a running PostgreSQL instance with a `finance_test` database:

```bash
psql -U finance_user -c "CREATE DATABASE finance_test;"
pytest
```

---

## Authentication

All protected routes require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token from `POST /auth/login`. Tokens expire after 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
