# 4Viso Backend

FastAPI + PostgreSQL backend for the 4Viso Cargo Intelligence Platform.

## Tech stack

- Python 3.11+
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.x (async)
- JWT authentication (python-jose)
- bcrypt password hashing
- SlowAPI rate limiting
- Pydantic v2

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 16 running locally or remotely
- pip

## Setup

### 1. Clone and navigate
```bash
cd backend
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```

Open `.env` and fill in:
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/4viso_db
SECRET_KEY=your-secret-key-min-32-chars
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Create the database
```sql
CREATE DATABASE 4viso_db;
```

### 6. Seed the database (first time only)
```bash
python seed.py
```

This creates all tables and populates:
- 12 nodes (warehouses, airports, ports, hubs across Europe, Asia, Americas)
- 7 carriers (Air, Road, Sea)
- 12 caretakers (all types)

Running seed.py a second time is safe — it skips if data already exists.

### 7. Start the server
```bash
uvicorn main:app --reload
```

Server runs at http://localhost:8000

## API documentation

Interactive Swagger UI available at http://localhost:8000/docs

## Project structure
backend/
├── main.py              # App entry point, CORS, error handlers
├── database.py          # Async SQLAlchemy engine and session
├── seed.py              # Database seeding script
├── models/
│   ├── user.py          # User, AccessLog, RefreshToken
│   └── lane.py          # Node, Carrier, Lane, LaneNode, LaneLeg, Caretaker
├── schemas/
│   ├── user.py          # Auth and user schemas
│   ├── lane.py          # Lane domain schemas
│   └── analytics.py     # Analytics response schemas
├── services/
│   ├── auth.py          # Auth logic, JWT, refresh tokens
│   ├── lane.py          # Lane CRUD and risk engine
│   ├── admin.py         # User management and audit logs
│   └── analytics.py     # Aggregation queries
├── routes/
│   ├── auth.py          # /auth/* with rate limiting
│   ├── lane.py          # /api/lanes, nodes, carriers, caretakers
│   ├── admin.py         # /api/admin/* (admin only)
│   └── analytics.py     # /api/analytics/*
└── middleware/
└── auth.py          # JWT bearer + role guards

## Roles and permissions

| Role | Read | Create/Edit lanes | Manage caretakers | Admin panel |
|---|---|---|---|---|
| user | ✅ | ❌ | ❌ | ❌ |
| port | ✅ | ❌ | ❌ | ❌ |
| auditor | ✅ | ❌ | ❌ | ❌ |
| staff | ✅ | ✅ | ✅ | ❌ |
| admin | ✅ | ✅ | ✅ | ✅ |

## First admin user

Register via the frontend or API, then run:
```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

## Rate limits

| Endpoint | Limit |
|---|---|
| POST /auth/register | 10 / minute |
| POST /auth/login | 20 / minute |
| POST /auth/refresh | 30 / minute |