# NGO Resource Allocation System

> Connect people in crisis to the nearest NGO with available resources — instantly.

---

## Problem Statement

During disasters, two critical problems happen simultaneously. Field workers and affected people have no fast way to report their needs — they rely on paper forms, phone calls, and WhatsApp messages that take hours to reach decision-makers. And NGOs have no live view of their own stock — food packs, medical kits, and vehicles are tracked in spreadsheets that are almost always outdated.

The result: people in need cannot find help, and NGOs dispatch resources without knowing what is actually available or where it is most needed.

---

## Solution Overview

A web platform with two distinct sides — one for affected users requesting help, one for NGOs managing and dispatching resources.

A user opens the app, describes their need, and shares their GPS location. The platform validates the request through two gates: first confirming the need is genuine, then checking whether matching stock exists in the NGO resource database. If both pass, a PostGIS-powered GPS engine finds the nearest NGO depot with the right resources available and returns the NGO's contact details and estimated response time to the user. The matched NGO receives an alert on their dashboard with the task details, and their stock is automatically depleted on dispatch.

On the NGO side, coordinators use an admin panel to log and update their available resources — food, medicine, shelter materials, vehicles — by depot location. A priority dashboard shows a live map of incoming requests ranked by severity and distance.

The entire backend is powered by GPT-4o via GitHub's free model API (using a GitHub Personal Access Token routed through the Azure inference endpoint), keeping costs at zero while retaining full GPT-4o quality.

**Stack:** FastAPI · PostgreSQL + PostGIS · Redis · GPT-4o via GitHub Models API · Tesseract OCR · Whisper STT · React / Next.js · Leaflet · Recharts · Railway · Vercel

---

## Features

### Dual-database architecture
Two separate databases with clear ownership: the NGO Resource DB stores stock, depot locations, and expiry data — owned and updated by NGO admins. The User Reports DB stores submitted field reports and help requests with GPS coordinates and severity scores. They are joined only at the matching layer, keeping concerns cleanly separated.

### Multi-modal field data ingestion
Field workers submit reports as images of paper forms, voice notes, or typed text. OCR, Whisper STT, and a text handler all converge into a single AI Structuring Agent that normalizes and extracts structured entities — location, need type, affected count, severity — into both databases.

### Two-stage request validation
When a user requests help, two sequential checks run before any NGO is contacted. The first confirms the request is genuine and the need is real (AI-powered classification). The second queries the NGO Resource DB to verify that matching stock actually exists. Requests that fail either gate are flagged or placed on a waitlist — no phantom dispatches.

### GPS-powered nearest NGO matching
Using PostGIS spatial queries, the platform calculates the distance between the user's GPS coordinates and every NGO depot that holds the requested resource type. It returns the closest match with sufficient stock, along with an estimated response time. Users see the matched NGO's name, address, and contact — not an abstract recommendation.

### Live resource inventory management
NGO admins log available stock through a simple admin panel: item name, category, quantity, unit, depot location (pin on map), and expiry date. When a dispatch is accepted, inventory is automatically depleted via a database transaction with row-level locking to prevent double-allocation.

### NGO priority dashboard
A React dashboard shows NGO coordinators a Leaflet map with incoming request pins ranked by severity and proximity to their depots, a pending task list, and a stock status panel with low-inventory warnings.

### Zero-cost GPT-4o via GitHub Models API
All AI agents use GPT-4o through GitHub's free model inference endpoint, authenticated with a GitHub Personal Access Token. No OpenAI billing account or Azure subscription required for the AI layer.

### Deploy-first architecture
The system is designed to be fully deployable before the chat interface or WebSocket layer is built. Phase 1 through 5 produce a working, live URL. Real-time features are additive enhancements, not prerequisites.

---

## Architecture
```
Field worker app          Affected user app
      │                         │
      └──────── API Gateway ────┘
                    │
          AI Structuring Agent
          (OCR / STT / Text → JSON)
           /                    \
  NGO Resource DB          User Reports DB
  (stock · depot · expiry)  (reports · GPS · severity)
                                 │
                    User submits help request + GPS
                                 │
                    Validation 1 — need check (AI)
                                 │
                    Validation 2 — stock check (DB)
                                 │
                    GPS nearest NGO finder (PostGIS)
                                 │
                    Match + ETA engine
                         /             \
             User gets NGO details    NGO gets alert + task
                                           │
                                    NGO admin panel
                                    (updates stock)
```

---

## GPT-4o via GitHub Models API (free)
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="YOUR_GITHUB_PAT_TOKEN",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "your prompt"}],
)
```

No billing. No Azure subscription. Just a GitHub account with a PAT token that has the `models:read` scope.