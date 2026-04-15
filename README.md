# NGO Resource Allocation Platform

> Connect people in crisis to the nearest NGO with available resources — instantly.

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://nextjs.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20+%20PostGIS-336791)](https://postgis.net/)
[![AI](https://img.shields.io/badge/AI-GPT--4o%20via%20GitHub%20Models-412991)](https://github.com/marketplace/models)

---

## Problem Statement

When disasters strike — floods, cyclones, droughts — NGOs face a chaotic information crisis. Field workers collect data through paper surveys, voice notes, and photographs. This data sits in disconnected silos: WhatsApp messages, physical forms, verbal reports. By the time it reaches a decision-maker, it is hours old, incomplete, and impossible to compare across regions.

Simultaneously, NGOs have no live view of their own resources. Food stocks, medical kits, shelter materials, and vehicles are tracked in spreadsheets that are almost always out of date.

The result: people in need cannot find help, and NGOs dispatch resources without knowing what is actually available or where it is most needed.

---

## Solution Overview

A full-stack AI platform with two distinct sides:

**For affected users** — Submit a help request via text, voice recording, or photo. Share your GPS location. The platform validates the request through two AI-powered gates, then uses PostGIS spatial queries to find the nearest NGO depot with matching available stock. The user gets the NGO's contact details and ETA within seconds.

**For NGO coordinators** — A live dashboard showing a color-coded map of incoming requests, a priority-ranked task list, inventory management, and one-click dispatch. Accepting a task automatically depletes stock with row-level locking to prevent double-dispatch.

All AI agents run on **GPT-4o via GitHub Models API** — completely free using a GitHub Personal Access Token.

---

## Architecture

```
Field worker / Affected user
         │
         ▼
   API Gateway (FastAPI)
         │
    ┌────┴────┐
    │         │
  OCR      Whisper STT    ← image / voice input
    │         │
    └────┬────┘
         │
  AI Structuring Agent (GPT-4o)
  extracts: location, need_type, severity
         │
    ┌────┴──────────────┐
    │                   │
User Reports DB     NGO Resource DB
(PostgreSQL+PostGIS) (PostgreSQL+PostGIS)
    │                   │
    └────────┬──────────┘
             │
   Validation Gate 1 — AI need check (GPT-4o)
             │
   Validation Gate 2 — Stock availability check (DB)
             │
   GPS Nearest NGO Finder (PostGIS ST_Distance)
             │
        ┌────┴────┐
        │         │
   User gets    NGO gets
   NGO details  alert + task
        │         │
        └────┬────┘
             │
      NGO Admin Dashboard
      (accept → stock depletes)
```

---

## Features

### Multi-modal field data ingestion
Submit reports as typed text, voice recordings (transcribed by Whisper), or photos of paper forms (OCR via Tesseract). All three converge into a single AI pipeline.

### Two-stage AI validation
Every request passes two sequential gates before any NGO is contacted. Gate 1 uses GPT-4o to verify the request is genuine. Gate 2 queries the database to confirm matching stock exists. Failed requests are either flagged or placed on a waitlist.

### GPS-powered nearest NGO matching
PostGIS `ST_Distance` and `ST_DWithin` queries find the closest NGO depot with available resources within 200km. Returns distance in km and estimated response time.

### Live resource inventory
NGOs log stock by category (FOOD, MEDICAL, SHELTER, WASH), quantity, unit, and GPS depot location. Stock depletes automatically on dispatch using row-level locking to prevent double-allocation.

### Real-time NGO dashboard
Live map with severity-colored pins (red = critical, amber = moderate, green = low), summary cards, task list with accept/decline/complete actions, and inventory management.

### Password reset flow
Forgot password generates a secure token valid for 30 minutes. Reset link sent via email (configurable via Gmail SMTP).

### Deploy-first architecture
Designed to be deployable before real-time features are added. Backend on Railway, frontend on Vercel, database on Neon (free tier with PostGIS).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI 0.111 + Uvicorn |
| Database | PostgreSQL 15 + PostGIS 3.5 (Neon) |
| ORM + Migrations | SQLAlchemy 2.0 + Alembic |
| AI Agents | GPT-4o via GitHub Models API |
| OCR | Tesseract + pytesseract |
| Speech-to-text | OpenAI Whisper API |
| Auth | JWT (python-jose) + bcrypt |
| Cache | Redis |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Maps | React Leaflet + OpenStreetMap |
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| Database hosting | Neon (free tier) |

---

## Project Structure

```
ngo-resource-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py           # register, login
│   │   │   ├── dashboard.py      # summary, map data, inventory
│   │   │   ├── deps.py           # JWT auth dependency
│   │   │   ├── feedback.py       # human-in-the-loop corrections
│   │   │   ├── health.py         # /health, /health/db
│   │   │   ├── password_reset.py # forgot/reset password
│   │   │   ├── reports.py        # submit, status polling
│   │   │   ├── resources.py      # NGO resource CRUD
│   │   │   └── tasks.py          # accept, decline, complete
│   │   ├── agents/
│   │   │   ├── client.py         # single GPT-4o client
│   │   │   ├── structuring.py    # entity extraction agent
│   │   │   └── validation.py     # need validation agent
│   │   ├── core/
│   │   │   ├── config.py         # pydantic settings
│   │   │   ├── database.py       # async SQLAlchemy engine
│   │   │   └── security.py       # JWT + bcrypt
│   │   ├── models/
│   │   │   ├── ngo_resource.py   # NgoUser + NgoResource ORM
│   │   │   └── user_report.py    # UserReport ORM
│   │   ├── processors/
│   │   │   ├── ocr.py            # Tesseract image → text
│   │   │   ├── stt.py            # Whisper audio → text
│   │   │   └── text.py           # ftfy normalization
│   │   ├── schemas/
│   │   │   ├── report.py         # request/response models
│   │   │   └── resource.py       # NGO resource models
│   │   ├── services/
│   │   │   ├── ingestion.py      # full AI pipeline orchestration
│   │   │   ├── matching.py       # PostGIS GPS matching
│   │   │   └── validation.py     # two validation gates
│   │   └── main.py               # FastAPI app + routers
│   ├── migrations/               # Alembic migration files
│   ├── tests/                    # pytest integration tests
│   ├── seed.py                   # demo data seeding script
│   ├── Dockerfile
│   ├── railway.toml
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── app/
    │   ├── dashboard/page.tsx    # NGO admin dashboard
    │   ├── forgot-password/      # forgot password page
    │   ├── login/page.tsx        # NGO login
    │   ├── register/page.tsx     # NGO registration
    │   ├── request/page.tsx      # user help request form
    │   ├── reset-password/       # password reset page
    │   ├── layout.tsx
    │   └── page.tsx              # landing page
    ├── components/
    │   └── DashboardMap.tsx      # Leaflet map component
    ├── lib/
    │   ├── api.ts                # all backend API calls
    │   └── auth.ts               # localStorage token helpers
    └── .env.local
```

---

## Local Development Setup

### Prerequisites

- Python 3.11 or 3.12
- Node.js 20+
- Git

### 1. Clone the repo

```bash
git clone https://github.com/Subhra-Nandi/ngo-resource-dashboard.git
cd ngo-resource-dashboard
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Neon PostgreSQL — get from neon.tech (free)
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/ngodb?ssl=require
DATABASE_URL_SYNC=postgresql://user:pass@ep-xxx.neon.tech/ngodb?sslmode=require

# Redis — use Redis Cloud free tier or Railway Redis addon
REDIS_URL=redis://localhost:6379

# GitHub PAT with models:read scope
# Create at: github.com → Settings → Developer Settings → PAT → Classic
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxx

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

APP_ENV=development
APP_NAME=NGO Resource Platform
```

### 4. Database setup

Create a free PostgreSQL database at [neon.tech](https://neon.tech). Enable PostGIS in the SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Version();
```

Run migrations:

```bash
alembic upgrade head
```

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

### 6. Frontend setup

```bash
cd ../frontend
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Frontend runs at `http://localhost:3000`

### 7. Seed demo data (optional)

With the backend running, seed realistic Sundarbans flood scenario data:

```bash
cd backend
python seed.py
```

This creates 3 NGO accounts with 9 resource depots and 8 help requests across South 24 Parganas.

---

## Deployment

### Backend → Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select the `ngo-resource-dashboard` repo
3. Set **Root Directory** to `backend`
4. Railway auto-detects the Dockerfile
5. Add these environment variables in Railway → Variables tab:

```
DATABASE_URL        postgresql+asyncpg://...neon.tech/ngodb?ssl=require
DATABASE_URL_SYNC   postgresql://...neon.tech/ngodb?sslmode=require
REDIS_URL           (auto-set if you add Railway Redis addon)
GITHUB_TOKEN        github_pat_xxxxx
SECRET_KEY          your_secret_key
ALGORITHM           HS256
ACCESS_TOKEN_EXPIRE_MINUTES  60
APP_ENV             production
APP_NAME            NGO Resource Platform
```

6. Deploy → your backend URL is shown in the Railway dashboard

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → Add New Project → Import from GitHub
2. Select `ngo-resource-dashboard`
3. Set **Root Directory** to `frontend`
4. Add environment variable:

```
NEXT_PUBLIC_API_URL = https://your-backend.railway.app
```

5. Deploy → your frontend URL is live

### Run migrations on production

After Railway deploys, run migrations against Neon once:

Temporarily set your local `.env` `DATABASE_URL` to the Neon production URL, then:

```bash
cd backend
alembic upgrade head
```

---

## API Endpoints

### Public endpoints (no auth required)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/health/db` | Database + PostGIS check |
| POST | `/auth/register` | Register new NGO |
| POST | `/auth/login` | NGO login, returns JWT |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| POST | `/requests/submit` | Submit text help request |
| POST | `/requests/submit-audio` | Submit voice help request |
| POST | `/requests/submit-image` | Submit photo help request |
| GET | `/requests/{id}/status` | Poll request status |

### NGO authenticated endpoints (Bearer token required)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/summary` | Summary cards |
| GET | `/dashboard/map-data` | GPS pins for map |
| GET | `/dashboard/inventory` | Current stock levels |
| GET | `/dashboard/requests/all` | All active requests |
| GET | `/ngo/tasks` | Pending tasks for this NGO |
| POST | `/ngo/tasks/{id}/accept` | Accept task + deplete stock |
| POST | `/ngo/tasks/{id}/decline` | Decline task |
| POST | `/ngo/tasks/{id}/complete` | Mark task complete |
| POST | `/ngo/resources` | Add resource to inventory |
| PUT | `/ngo/resources/{id}/quantity` | Update stock quantity |
| DELETE | `/ngo/resources/{id}` | Remove resource |
| POST | `/feedback` | Submit recommendation override |

---

## How the AI Pipeline Works

```
User submits request (text / voice / photo)
              │
    ┌─────────┴──────────┐
   OCR               Whisper STT
  (photos)           (voice notes)
    └─────────┬──────────┘
              │
       Text normalization
       (ftfy + langdetect)
              │
    GPT-4o Structuring Agent
    extracts:
    • location_name
    • need_type (FOOD/MEDICAL/SHELTER/WASH/OTHER)
    • severity (1-5)
    • affected_count
    • confidence score
              │
    Validation Gate 1 — GPT-4o
    "Is this request genuine?"
    confidence < 0.8 → FLAGGED
              │
    Validation Gate 2 — Database
    "Does matching stock exist?"
    no stock → WAITLIST
              │
    PostGIS GPS Matching
    ST_Distance + ST_DWithin
    finds nearest NGO within 200km
              │
    Report status → MATCHED
    User sees NGO details + ETA
```

---

## GitHub Models API (Free GPT-4o)

This project uses GPT-4o for free via GitHub's model inference endpoint.

**Setup:**

1. Go to `github.com` → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate new token with **`models:read`** scope
3. Add to `.env` as `GITHUB_TOKEN`

**Usage in code:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="YOUR_GITHUB_PAT",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

No billing. No Azure subscription needed. Just a GitHub account.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'add: my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

Built for disaster relief NGOs operating in the Sundarbans delta region of West Bengal, India — one of the world's most flood-prone areas.

Stack: FastAPI · Next.js · PostgreSQL · PostGIS · GPT-4o · Tesseract · Leaflet · Railway · Vercel · Neon