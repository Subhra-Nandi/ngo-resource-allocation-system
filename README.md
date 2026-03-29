# NGO Resource Allocation System

> Bridging the gap between unstructured field data and life-saving decisions.

---

## Problem Statement

When disasters strike — floods, cyclones, droughts — NGOs face a chaotic information crisis. Field workers collect data through paper surveys, voice notes, and photographs. This data sits in disconnected silos: WhatsApp messages, physical forms, verbal reports. By the time it reaches a decision-maker, it is hours old, incomplete, and impossible to compare across regions.

The result: resources get sent where they were needed yesterday, not where they are needed now. Duplicate aid reaches some zones while others are completely missed. Teams operate on gut instinct rather than ground truth.

The core problem is not a lack of data — it is that the data is **unstructured, decentralized, and analog**, making real-time resource allocation nearly impossible.

---

## Solution Overview

The NGO Resource Allocation Platform is a full-stack AI system that converts raw, messy field inputs — images of paper forms, voice notes, typed messages — into a live, prioritized, geospatial intelligence dashboard that tells NGO coordinators exactly where to send resources and why.

Field workers submit reports from any device using a mobile-first web app. The platform automatically processes each submission through an AI pipeline: OCR extracts text from images, Whisper transcribes voice notes, and a two-stage LLM agent extracts structured entities and maps them to a validated schema. Every validated report is scored, classified by resource type, and surfaced on a real-time dashboard within seconds.

A Decision Agent powered by RAG (Retrieval-Augmented Generation) queries similar historical situations to generate specific allocation recommendations. A Simulation Engine lets coordinators test proposed resource changes and see projected impact before committing — a what-if sandbox for disaster response.

**Stack:** FastAPI · PostgreSQL + PostGIS · Redis · Azure OpenAI (GPT-4o / GPT-4o mini) · Azure Whisper · React / Next.js · Leaflet · Recharts · FAISS

---

## Features

### Multi-modal field data ingestion
Field workers submit reports as images (photos of paper forms), voice recordings, or plain text. All three paths converge into a single normalized text pipeline with automatic language detection — supporting English, Hindi, Bengali, and other Indian languages out of the box.

### AI structuring pipeline
A two-stage LLM agent pipeline first extracts raw entities (locations, affected counts, time references, urgency signals) and then maps them to a strict Pydantic schema with confidence scoring. A validation layer flags low-confidence records for human review and retries failed extractions with enriched context, keeping data quality high.

### Geospatial priority scoring
Every validated report is scored using a weighted formula across severity, recency, affected population, and remoteness. Scores are cached in Redis and updated continuously. Regions are ranked so coordinators always know the highest-priority situation at a glance.

### Resource need classification
Reports are automatically grouped by resource type — Food & Water, Medical, Shelter, WASH, Psychosocial — and aggregated per region. Each NGO department sees only the category relevant to their team.

### RAG-powered decision agent
The Decision Agent retrieves semantically similar past situations from a FAISS vector store and uses them as context to generate specific, explainable allocation recommendations: what resource, how much, to which region, and why.

### Simulation engine
Coordinators can propose a resource reallocation — "what if I redirect two food trucks from Zone A to Zone C?" — and instantly see projected changes to priority scores across all regions. Decisions can be tested before real resources move.

### Real-time dashboard
A live React dashboard shows a Leaflet map with report pins color-coded by severity, a priority-ranked situation list, need-type breakdown charts, trend graphs, and a simulation panel — all updating in real time via Server-Sent Events.

### Human-in-the-loop feedback
When a coordinator overrides a recommendation, the correction is logged with a reason and fed back into the system as a training signal. The platform improves with every human correction.

### Error handling & observability
Invalid or ambiguous reports are routed to an error queue with structured flags rather than silently dropped. Every pipeline stage emits structured logs so the team can trace any report from raw input to dashboard pin.
