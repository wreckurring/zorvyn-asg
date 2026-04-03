# Finance Dashboard API

A role-based finance dashboard backend built with **FastAPI**, **PostgreSQL**, and **JWT authentication**. Supports full transaction CRUD, analytics endpoints, and fine-grained access control across three user roles.

---

## Innovative Features

These go beyond standard CRUD and are what differentiate this implementation:

### 1. Statistical Anomaly Detection — `GET /dashboard/anomalies`
Flags transactions that are statistical outliers within their category using **z-score analysis**. For any category with 3+ transactions, computes mean and standard deviation, then surfaces transactions where `amount > mean + N * std_dev`. The threshold `N` is configurable (`?z_threshold=2.0` by default). Each result includes `z_score`, `category_avg`, and `category_std` so consumers can understand why it was flagged.

### 2. Financial Insights Engine — `GET /dashboard/insights`
Synthesizes multiple data points into a single actionable snapshot:
- **Savings rate** — `(net_balance / total_income) * 100`
- **Month-over-month expense change** — compares current vs previous calendar month
- **Top expense category** — where the most money is going
- **Average daily spend** — total expenses divided by distinct days with transactions
- **Largest transaction** — id + amount for quick drill-down

### 3. Budget Management with Variance Tracking — `/budgets` + `GET /dashboard/budget-status`
Full CRUD for monthly budgets per category (unique constraint on `category + month`). The `/dashboard/budget-status?month=YYYY-MM` endpoint merges budget limits against actual spend and returns per-category:
- `budget` — the set limit
- `actual` — real spend that month
- `variance` — how much is left (negative = over)
- `utilization_pct` — percentage of budget consumed
- `status` — `under_budget`, `over_budget`, or `no_budget` (spent but no limit set)

### 4. Audit Trail — `GET /audit-logs`
Every transaction create, update, and delete is logged with the acting user, resource ID, and a human-readable `details` string (e.g., `amount=2500.0`). Queryable by `resource_type` and `user_id`. Critical for any real finance system — demonstrates awareness of compliance and auditability requirements.

### 5. CSV Export with Filters — `GET /transactions/export`
Streams a filtered CSV of transactions using FastAPI's `StreamingResponse`. Accepts all the same filters as the list endpoint (`type`, `category`, `date_from`, `date_to`, `created_by_me`). No memory spike for large exports.

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

### Alternative: run everything with Docker

```bash
docker-compose up --build
```

Starts PostgreSQL and the API together. Migrations run automatically on startup.

API docs available at: `http://localhost:8000/docs`

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user (rate limited: 10/min) |
| POST | `/auth/login` | Login — returns `access_token` + `refresh_token` (rate limited: 20/min) |
| POST | `/auth/refresh` | Issue new token pair from a valid refresh token |
| POST | `/auth/logout` | Logout (client must discard tokens) |
| GET | `/auth/me` | Get current user profile |
| PATCH | `/auth/me` | Update own email or password |

### Users (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get a single user |
| POST | `/users` | Create a user |
| PATCH | `/users/{id}/role` | Change a user's role |
| PATCH | `/users/{id}/status` | Activate or deactivate a user |

### Transactions

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/transactions` | List transactions (filterable, paginated) | All |
| GET | `/transactions/stats` | Aggregates per category (count, total, avg, min, max) | All |
| GET | `/transactions/export` | Download filtered transactions as CSV | All |
| GET | `/transactions/{id}` | Get a single transaction | All |
| POST | `/transactions` | Create a transaction | Analyst, Admin |
| PUT | `/transactions/{id}` | Update a transaction | Admin |
| DELETE | `/transactions/{id}` | Soft delete a transaction | Admin |

**Query filters for `GET /transactions`:**
- `type` — `income` or `expense`
- `category` — partial match
- `date_from` / `date_to` — ISO date range
- `skip` / `limit` — pagination

**Response shape:**
```json
{ "total": 42, "skip": 0, "limit": 50, "results": [...] }
```

### Dashboard

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/dashboard/summary` | Total income, expenses, net balance (supports `?date_from` / `?date_to`) | All |
| GET | `/dashboard/by-category` | Totals grouped by category (supports date range) | All |
| GET | `/dashboard/categories` | Distinct categories in use (supports `?type`) | All |
| GET | `/dashboard/trends/monthly` | Monthly income vs expense breakdown | All |
| GET | `/dashboard/trends/weekly` | Weekly income vs expense breakdown | All |
| GET | `/dashboard/recent` | Last N transactions (`?limit=10`) | All |

### Budgets

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/budgets` | List budgets (filterable by `?month`) | All |
| POST | `/budgets` | Create a monthly budget for a category | Analyst, Admin |
| PATCH | `/budgets/{id}` | Update budget limit | Admin |
| DELETE | `/budgets/{id}` | Delete a budget | Admin |
| GET | `/dashboard/budget-status` | Actual vs budget per category for a month | All |

### Analytics (Innovative)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/dashboard/anomalies` | Statistical outlier detection per category (`?z_threshold=2.0`) | All |
| GET | `/dashboard/insights` | Savings rate, MoM change, top category, avg daily spend | All |

### Audit Logs (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/audit-logs` | Paginated log of all create/update/delete actions (filterable by `resource_type`, `user_id`) |

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
