# Finance Dashboard API

A production-grade finance dashboard backend with **role-based access control**, **JWT authentication**, and **analytics** — built with FastAPI and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)

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

---

### 2. Financial Insights Engine — `GET /dashboard/insights`

Synthesizes multiple data points into a **single actionable snapshot** without requiring multiple round-trips.

---

### 3. Budget Management with Variance Tracking

Full CRUD for monthly per-category budgets. The `category + month` combination is unique-constrained at the database level.

`GET /dashboard/budget-status?month=2024-01` merges budgets against actual spend and returns:

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
│   ├── main.py                  
│   ├── config.py                
│   ├── database.py               
│   ├── limiter.py                
│   ├── models/
│   │   ├── user.py               
│   │   ├── transaction.py        
│   │   ├── audit_log.py          
│   │   └── budget.py             
│   ├── schemas/
│   │   ├── auth.py               
│   │   ├── user.py               
│   │   ├── transaction.py        
│   │   ├── dashboard.py          
│   │   ├── budget.py             
│   │   └── audit.py              
│   ├── routers/
│   │   ├── auth.py               
│   │   ├── users.py              
│   │   ├── transactions.py       
│   │   ├── dashboard.py         
│   │   ├── budgets.py            
│   │   └── audit.py             
│   ├── services/
│   │   ├── auth_service.py       
│   │   ├── user_service.py       
│   │   ├── transaction_service.py
│   │   ├── dashboard_service.py  
│   │   ├── budget_service.py     
│   │   └── audit_service.py     
│   └── middleware/
│       ├── access_control.py     # get_current_user, require_roles factory
│       └── logging.py            # Request ID + timing middleware
├── alembic/
│   └── versions/
├── tests/
├── Dockerfile
├── alembic.ini
├── seed.py
├── pytest.ini
└── requirements.txt
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