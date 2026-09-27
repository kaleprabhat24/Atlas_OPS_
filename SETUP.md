# ATLAS-OPS — Complete Setup Guide

> **One file, every step.** Follow these instructions to run the full ATLAS-OPS platform locally.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR LOCAL MACHINE                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend    │  │   Backend    │  │  PostgreSQL   │  │
│  │  React+Vite   │→ │   FastAPI    │→ │   (pgAdmin)   │  │
│  │  Port 5173    │  │  Port 8000   │  │   Port 5432   │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  │
│                           │                              │
│                    ┌──────┴───────┐                      │
│                    │    Redis     │ ← Docker Container   │
│                    │  Port 6379   │                      │
│                    └──────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

| Component    | Runs On        | How                          |
|-------------|----------------|------------------------------|
| PostgreSQL  | **Local**      | pgAdmin / native install     |
| Redis       | **Docker**     | `docker compose up`          |
| Backend     | **Local**      | `python run_local.py`        |
| Frontend    | **Local**      | `npm run dev`                |

---

## Prerequisites

Install these before starting:

| Tool        | Download                                        | Verify Command      |
|------------|------------------------------------------------|---------------------|
| Python 3.12+ | https://www.python.org/downloads/             | `python --version`  |
| Node.js 18+  | https://nodejs.org/                            | `node --version`    |
| Docker Desktop | https://www.docker.com/products/docker-desktop | `docker --version`  |
| PostgreSQL + pgAdmin | https://www.postgresql.org/download/windows/ | `psql --version` |
| Git        | https://git-scm.com/                            | `git --version`     |

---

## Step-by-Step Setup

### STEP 1: Clone the Repository

```powershell
git clone https://github.com/tailormst/Atlas_OPS.git
cd Atlas_OPS
```

---

### STEP 2: Set Up PostgreSQL Database (pgAdmin)

#### Option A: Using the setup script (recommended)
```powershell
pip install psycopg2-binary
python setup_db.py
```

#### Option B: Using pgAdmin UI
1. Open **pgAdmin 4**
2. Connect to your PostgreSQL server (usually `localhost:5432`)
3. Right-click **Databases** → **Create** → **Database**
4. Name: `atlas_ops`
5. Owner: `postgres` (or your username)
6. Click **Save**

#### Option C: Using psql command line
```powershell
psql -U postgres -c "CREATE DATABASE atlas_ops;"
```

---

### STEP 3: Configure Environment Variables

```powershell
copy .env.example .env
```

Now **edit `.env`** and update the `DATABASE_URL` with your actual PostgreSQL credentials:

```env
# If your pgAdmin password is "mypassword" and username is "postgres":
DATABASE_URL=postgresql+asyncpg://postgres:mypassword@localhost:5432/atlas_ops
```

> **How to find your credentials:**
> - Open pgAdmin → click your server → Properties tab
> - **Username**: usually `postgres`
> - **Password**: whatever you set during PostgreSQL installation
> - **Port**: usually `5432`

---

### STEP 4: Start Redis (Docker)

```powershell
docker compose up -d
```

Verify Redis is running:
```powershell
docker ps
# Should show: atlas_redis running on port 6379
```

---

### STEP 5: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

---

### STEP 6: Start the Backend

```powershell
python run_local.py
```

You should see:
```
Starting ATLAS-OPS in LOCAL mode...
INFO: redis_connected
INFO: ML models loaded
INFO: database_tables_created
INFO: atlas_ops_ready host=0.0.0.0 port=8000
```

Verify: Open http://localhost:8000/docs — you should see the FastAPI Swagger docs.

> **If you see "DATABASE CONNECTION FAILED":**
> - Ensure PostgreSQL is running in pgAdmin
> - Check your `.env` file — update `DATABASE_URL` with correct username/password
> - Run `python setup_db.py` to create the database

---

### STEP 7: Install Frontend Dependencies

Open a **new terminal** (keep the backend running):

```powershell
cd frontend
npm install
```

---

### STEP 8: Start the Frontend

```powershell
npm run dev
```

You should see:
```
VITE v6.x.x  ready in XXXms

  ➜  Local:   http://localhost:5173/
```

---

### STEP 9: Open the Application

Open your browser and go to: **http://localhost:5173/**

You should see:
- ✅ ATLAS-OPS Dashboard with stats cards
- ✅ Gateway health cards
- ✅ "API Connected" indicator in the header (green dot)
- ✅ Recent transactions list

---

## Using the Application

### Dashboard (http://localhost:5173/)
- Real-time gateway health metrics
- Auto-refreshes every 10 seconds
- Stats cards, fraud chart, recent transactions

### Live Pipeline (http://localhost:5173/live)
1. Choose a preset: **Normal**, **High-Risk**, or **Medium Risk**
2. Click **⚡ Process Transaction**
3. Watch all 16 pipeline stages animate in real time:
   - Transaction Submitted → Validation → Luhn Check → Fraud Scoring → Gateway Routing → Execution → AI Explanation → Result
4. See live metrics panel: fraud score, gateway, latency, circuit state
5. Read scrolling logs in the log panel

### Admin Panel (http://localhost:5173/admin)
- View ML model status (loaded vs fallback)
- Simulate gateway outages (requires admin key from `.env` SECRET_KEY)

---

## Quick Reference: Terminal Commands

```powershell
# ── Terminal 1: Redis (Docker) ──────────────────────────────────
docker compose up -d

# ── Terminal 2: Backend (Python) ────────────────────────────────
python run_local.py

# ── Terminal 3: Frontend (Node.js) ──────────────────────────────
cd frontend
npm run dev
```

---

## Stopping Everything

```powershell
# Stop frontend:  Ctrl+C in Terminal 3
# Stop backend:   Ctrl+C in Terminal 2
# Stop Redis:
docker compose down
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Black screen in browser** | Ensure you're on `http://localhost:5173/` not `8000` |
| **"API Offline" in header** | Backend isn't running — start with `python run_local.py` |
| **DATABASE CONNECTION FAILED** | Check `.env` credentials, ensure PostgreSQL runs in pgAdmin |
| **Redis connection failed** | Run `docker compose up -d`, verify with `docker ps` |
| **npm install fails** | Delete `frontend/node_modules` and `package-lock.json`, retry |
| **Port 5432 in use** | Another PostgreSQL instance running? Check pgAdmin |
| **Port 8000 in use** | Kill the process: `taskkill /F /IM python.exe` |
| **Port 5173 in use** | Kill the process or change port in `vite.config.js` |

---

## Project Structure

```
Atlas_OPS/
├── app/                          # FastAPI Backend
│   ├── main.py                   # App entrypoint
│   ├── api/                      # API routes
│   │   ├── transaction.py        # POST /v1/transaction/process
│   │   ├── pipeline.py           # POST /v1/transaction/process-live (SSE)
│   │   ├── gateways.py           # GET  /v1/gateways/health
│   │   ├── explain.py            # GET  /v1/transaction/{id}/explain
│   │   ├── simulate.py           # POST /v1/simulate/outage
│   │   └── ml.py                 # GET  /v1/ml/status
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Environment settings
│   │   ├── database.py           # PostgreSQL connection
│   │   ├── redis_client.py       # Redis connection
│   │   ├── circuit_breaker.py    # Per-gateway circuit breakers
│   │   ├── idempotency.py        # Request deduplication
│   │   └── logging.py            # Structured JSON logging
│   ├── models/                   # Database models + schemas
│   ├── services/                 # Business logic
│   └── ml_models/                # ML model files (.pkl)
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── App.jsx               # Root + routing
│   │   ├── pages/                # Dashboard, LiveDemo, Admin
│   │   ├── components/           # UI components
│   │   ├── api/client.js         # Backend API client
│   │   └── store/useStore.js     # Zustand state
│   ├── package.json
│   └── vite.config.js
├── .env                          # Your local config (not in git)
├── .env.example                  # Template for .env
├── docker-compose.yml            # Redis only
├── requirements.txt              # Python dependencies
├── setup_db.py                   # Database creation script
├── run_local.py                  # Backend startup script
└── SETUP.md                      # ← This file
```
