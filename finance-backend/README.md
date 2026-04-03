# Finance Dashboard API

A production-grade finance dashboard backend with **role-based access control**, **JWT authentication**, and **analytics** — built with FastAPI and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Tests](https://img.shields.io/badge/tests-93%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Innovative Features

These go beyond standard CRUD and are what set this implementation apart.

### 1. Statistical Anomaly Detection — `GET /dashboard/anomalies`

Flags transactions that are **statistical outliers** within their category using z-score analysis.

For any category with 3+ transactions, computes the mean and standard deviation. Returns transactions where:

```
amount > mean + (z_threshold × std_dev)
```

The threshold is tunable via `?z_threshold` (default `2.0`, range `1.0–4.0`). Results are sorted by z-score descending and include `category_avg` and `category_std` so consumers understand exactly *why* a transaction was flagged.

**Example response:**
```json
[
  {
    "transaction_id": 47,
    "date": "2024-03-15",
    "category": "Groceries",
    "type": "expense",
    "amount": 1850.00,
    "category_avg": 320.50,
    "category_std": 45.20,
    "z_score": 3.38
  }
]
```

---

### 2. Financial Insights Engine — `GET /dashboard/insights`

Synthesizes multiple data points into a **single actionable snapshot** without requiring multiple round-trips.

| Field | What it measures |
|---|---|
| `savings_rate_pct` | `(net_balance / total_income) × 100` |
| `top_expense_category` | Category with highest total spend |
| `month_over_month_expense_change_pct` | % change vs previous calendar month |
| `current_month_net` | Income minus expenses for the current month |
| `avg_daily_expense` | Total expenses ÷ distinct days with transactions |
| `avg_transaction_amount` | Mean transaction value across all records |
| `largest_transaction_id` / `largest_transaction_amount` | Quick pointer to the biggest single transaction |

---

### 3. Budget Management with Variance Tracking

Full CRUD for monthly per-category budgets. The `category + month` combination is unique-constrained at the database level.

`GET /dashboard/budget-status?month=2024-01` merges budgets against actual spend and returns:

```json
[
  {
    "category": "Rent",
    "month": "2024-01",
    "budget": 3500.00,
    "actual": 3200.00,
    "variance": 300.00,
    "utilization_pct": 91.4,
    "status": "under_budget"
  },
  {
    "category": "Dining",
    "month": "2024-01",
    "budget": 0.0,
    "actual": 640.00,
    "variance": -640.00,
    "utilization_pct": 0.0,
    "status": "no_budget"
  }
]
```

`status` is one of `under_budget`, `over_budget`, or `no_budget` (money spent but no limit set).

---

### 4. Immutable Audit Trail — `GET /audit-logs`

Every transaction `create`, `update`, and `delete` is logged with the acting user, resource ID, and a human-readable `details` string (e.g. `amount=2500.0, category=Rent`). Queryable by `resource_type` and `user_id` with pagination.

Finance systems have compliance requirements. This demonstrates awareness of auditability beyond functional requirements.

---

### 5. Streaming CSV Export — `GET /transactions/export`

Uses FastAPI's `StreamingResponse` to stream a filtered CSV directly without buffering the full dataset in memory. Accepts all the same filters as the list endpoint — useful for finance teams that need data in spreadsheets.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | FastAPI 0.111 | Auto-generates OpenAPI docs, Pydantic validation, async-ready |
| Database | PostgreSQL 16 | ACID compliance, window functions, production standard |
| ORM | SQLAlchemy 2.0 | Type-safe mapped columns, connection pooling |
| Migrations | Alembic | Versioned, reversible schema changes |
| Auth | JWT via python-jose | Stateless, access + refresh token pair |
| Password hashing | passlib/bcrypt | Industry standard |
| Validation | Pydantic v2 | Request/response contracts enforced at the boundary |
| Rate limiting | slowapi | Protects auth endpoints from brute force |
| Testing | pytest + httpx | Integration tests against real PostgreSQL |
| Containers | Docker + Compose | One-command local setup |

---

## Project Structure

```
finance-backend/
├── app/
│   ├── main.py                   # App entry, middleware, exception handlers
│   ├── config.py                 # Settings loaded from .env
│   ├── database.py               # Engine, session, Base
│   ├── limiter.py                # Rate limiter instance
│   ├── models/
│   │   ├── user.py               # User, UserRole enum
│   │   ├── transaction.py        # Transaction, TransactionType enum
│   │   ├── audit_log.py          # AuditLog, AuditAction enum
│   │   └── budget.py             # Budget (category + month limits)
│   ├── schemas/
│   │   ├── auth.py               # LoginRequest, TokenResponse, RefreshRequest
│   │   ├── user.py               # UserCreate, UserResponse, UserProfileUpdate
│   │   ├── transaction.py        # TransactionCreate/Update/Response, PaginatedTransactions
│   │   ├── dashboard.py          # SummaryResponse, AnomalyRecord, InsightsResponse, ...
│   │   ├── budget.py             # BudgetCreate, BudgetResponse, BudgetStatus
│   │   └── audit.py              # AuditLogResponse, PaginatedAuditLogs
│   ├── routers/
│   │   ├── auth.py               # register, login, refresh, logout, me, update me
│   │   ├── users.py              # user CRUD + role/status management
│   │   ├── transactions.py       # transaction CRUD + stats + export
│   │   ├── dashboard.py          # summary, trends, anomalies, insights, budget-status
│   │   ├── budgets.py            # budget CRUD
│   │   └── audit.py              # audit log query
│   ├── services/
│   │   ├── auth_service.py       # JWT creation/decoding, password hashing
│   │   ├── user_service.py       # user queries and updates
│   │   ├── transaction_service.py # transaction queries, stats, export
│   │   ├── dashboard_service.py  # aggregations, anomaly detection, insights
│   │   ├── budget_service.py     # budget CRUD and variance calculation
│   │   └── audit_service.py      # audit log write and query
│   └── middleware/
│       ├── access_control.py     # get_current_user, require_roles factory
│       └── logging.py            # Request ID + timing middleware
├── alembic/
│   └── versions/
│       ├── 69ce38c3_initial_schema.py
│       ├── 69cedc89_add_audit_logs.py
│       ├── 69cf53e4_add_performance_indexes.py
│       └── 69cf6103_add_budgets.py
├── tests/
│   ├── conftest.py               # Test DB setup, shared helpers
│   ├── test_auth.py
│   ├── test_rbac.py
│   ├── test_transactions.py
│   ├── test_users.py
│   ├── test_dashboard.py
│   ├── test_profile.py
│   ├── test_export.py
│   ├── test_stats.py
│   ├── test_audit.py
│   ├── test_categories.py
│   ├── test_budgets.py
│   ├── test_refresh_token.py
│   └── test_anomalies_insights.py
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── seed.py
├── pytest.ini
├── requirements.txt
├── .env.example
└── .dockerignore
```

---

## Quick Start

### Option A — Docker (recommended)

```bash
git clone <repo-url>
cd finance-backend
cp .env.example .env

docker-compose up --build
```

That's it. Docker Compose starts PostgreSQL, waits for it to be healthy, runs Alembic migrations, then starts the API.

**API:** `http://localhost:8000`
**Docs:** `http://localhost:8000/docs`

---

### Option B — Local

**Prerequisites:** Python 3.11+, PostgreSQL 16 running locally.

```bash
git clone <repo-url>
cd finance-backend

pip install -r requirements.txt
cp .env.example .env        # edit DATABASE_URL if needed

docker-compose up -d db     # start only the DB container

python -m alembic upgrade head
uvicorn app.main:app --reload
```

---

### Seed Demo Data

```bash
python seed.py
```

Creates 3 users and 15 transactions across Jan–Mar 2024:

| Role | Username | Password |
|---|---|---|
| admin | `admin` | `Admin@1234` |
| analyst | `analyst` | `Analyst@1234` |
| viewer | `viewer` | `Viewer@1234` |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | JWT signing secret (use a long random string in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `ALGORITHM` | No | `HS256` | JWT algorithm |

---

### Users *(Admin only)*

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get a single user |
| POST | `/users` | Create a user |
| PATCH | `/users/{id}/role` | Change role (`viewer` / `analyst` / `admin`) |
| PATCH | `/users/{id}/status` | Activate or deactivate (cannot deactivate yourself) |

---

### Dashboard

| Method | Endpoint | Roles | Description |
|---|---|---|---|
| GET | `/dashboard/summary` | All | Income, expenses, net balance (supports date range) |
| GET | `/dashboard/by-category` | All | Totals per category (supports date range) |
| GET | `/dashboard/categories` | All | Distinct categories (`?type=income\|expense`) |
| GET | `/dashboard/trends/monthly` | All | Monthly breakdown |
| GET | `/dashboard/trends/weekly` | All | ISO-week breakdown |
| GET | `/dashboard/recent` | All | Last N transactions (`?limit=10`) |
| GET | `/dashboard/anomalies` | All | Statistical outliers (`?z_threshold=2.0`) |
| GET | `/dashboard/insights` | All | Savings rate, MoM change, top category, daily avg |
| GET | `/dashboard/budget-status` | All | Budget vs actual for a month (`?month=YYYY-MM`) |

---

## Access Control

| Action | Viewer | Analyst | Admin |
|---|---|---|---|
| View transactions / dashboard | ✓ | ✓ | ✓ |
| Create transaction | — | ✓ | ✓ |
| Create budget | — | ✓ | ✓ |
| Update / delete transaction | — | — | ✓ |
| Update / delete budget | — | — | ✓ |
| Manage users | — | — | ✓ |
| View audit logs | — | — | ✓ |

Enforcement is done via **FastAPI dependency injection** — `require_roles(*roles)` is a factory that returns a dependency injected per route. No scattered `if` checks anywhere in the codebase.

---

## Authentication Flow

```
POST /auth/register  →  user created, role = viewer
POST /auth/login     →  { access_token (60min), refresh_token (7d) }

# Use access token on every protected request:
GET /transactions
Authorization: Bearer <access_token>

# When access token expires:
POST /auth/refresh
{ "refresh_token": "<refresh_token>" }
→ { new access_token, new refresh_token }

# Logout (client-side):
POST /auth/logout  →  200 OK  (client discards both tokens)
```

Access tokens carry `type: access`. Refresh tokens carry `type: refresh`. Using an access token as a refresh token (or vice versa) is explicitly rejected.

---

## Design Decisions

**Why PostgreSQL over SQLite**
ACID compliance matters for financial data. PostgreSQL also gives us `stddev_pop` for anomaly detection, `to_char` for date formatting in trend queries, and proper connection pooling.

**Why soft delete**
Transactions are never hard-deleted. `is_deleted = true` hides them from all queries but keeps the audit trail intact. Deleting financial records is a compliance risk.

**Why Alembic over `create_all`**
`create_all` on startup is fine for prototypes but makes it impossible to evolve the schema safely in production. Every schema change here is a versioned, reversible migration.

**Why dependency-injected role guards**
`require_roles(UserRole.admin)` is declared once and injected per route. This means RBAC enforcement is visible at the route definition, testable in isolation, and cannot be accidentally bypassed by forgetting an `if` check inside a handler.

**Why access + refresh tokens**
Short-lived access tokens (60 min) limit the blast radius of a stolen token. Refresh tokens (7 days) let clients stay authenticated without re-entering credentials. The `type` claim in the JWT payload prevents token-type confusion attacks.

**Why `created_by_me` as a query param**
Rather than a separate `/my-transactions` route, a boolean filter keeps the API surface flat and allows the same pagination and filtering logic to be reused.

---

## Running Tests

The test suite runs against a real PostgreSQL instance (not mocks). The `finance_test` database is created automatically on first run.

```bash
# Start the database
docker-compose up -d db

# Run all tests
pytest

# Run with output
pytest -v

# Run a specific file
pytest tests/test_anomalies_insights.py -v
```

**93 tests** across 13 test files covering auth, RBAC, transactions, dashboard, budgets, anomalies, insights, audit logs, CSV export, and token refresh.

---