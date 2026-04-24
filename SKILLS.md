# ThirdEye AI Contributor Guide

This file is the source of truth for any coding model (or developer) that needs to understand, run, and modify this project safely.

Goal: reduce onboarding time to under 10 minutes and prevent changes based on stale assumptions.

---

## 1) Project in One Minute

ThirdEye is a missing-person intelligence system.

Core loop:
1. A user creates a person profile and uploads reference photos.
2. The backend extracts face embeddings from those photos.
3. Background workers scan public sources for candidate images.
4. Candidate faces are embedded and compared with references.
5. Matches above threshold are stored, surfaced on dashboard, and optionally alerted.
6. Location history drives map and timeline views.

Main stack:
- Backend: FastAPI + APScheduler + async workers
- DB: PostgreSQL (primary) with SQLite fallback
- Frontend: React + Vite + Leaflet
- Face matching: InsightFace when available, deterministic simulation fallback otherwise

---

## 2) Repo Map (High Signal Files)

Backend:
- backend/main.py: app startup/shutdown, REST API, WebSocket endpoint
- backend/scheduler.py: recurring jobs, worker fan-out, result processing
- backend/models.py: Pydantic request/response/internal models
- backend/database.py: DB abstraction (Postgres + SQLite fallback)
- backend/face_engine.py: embedding extraction and similarity scoring
- backend/radius_manager.py: radius expansion and epicenter reset
- backend/alerts.py: email/SMS alert dispatch
- backend/workers/: source-specific crawlers/processors

Frontend:
- frontend/src/pages/Landing.jsx: intake UI
- frontend/src/pages/Dashboard.jsx: live dashboard and tabbed views
- frontend/src/hooks/useWebSocket.js: WS reconnect + event ingestion
- frontend/src/utils/api.js: frontend API client contract
- frontend/src/components/: map, timeline, cards, stats, upload, share

Infra/config:
- requirements.txt: backend deps
- frontend/package.json: frontend deps/scripts
- docker-compose.yml: local full-stack services
- env.example: expected environment variables
- database/schema.sql: Postgres schema bootstrap
- graphify-out/GRAPH_REPORT.md: graph-level architecture summary

---

## 3) Runtime Architecture

Startup (backend/main.py lifespan):
1. Connect DB.
2. Create AlertSystem, RadiusManager, SearchScheduler.
3. Start scheduler jobs.

Scheduler jobs (backend/scheduler.py):
- run_web_crawl: every SCAN_INTERVAL_HOURS (default 6)
- run_camera_scan: every CAM_SCAN_INTERVAL_MINUTES (default 10)
- check_radius_expansions: hourly

Worker execution model:
- All enabled workers run in parallel via asyncio.gather.
- Every worker implements BaseWorker.search(person) -> list[SearchResult].
- BaseWorker.safe_search wraps errors and returns [] on failure.

Result processing model:
1. Obtain candidate image bytes (from image_data or image_url).
2. Extract candidate embedding.
3. Compare against all reference embeddings for person.
4. If score < log threshold, drop.
5. Otherwise persist match (+ location when coordinates exist).
6. Broadcast WebSocket new_match event.
7. If alert threshold met, send alerts and reset epicenter if coords exist.

---

## 4) True Threshold Behavior

Defined in backend/face_engine.py:
- should_log(score): score >= 0.65
- should_alert(score): score >= 0.75

Label mapping (summary):
- >= 0.90: DEFINITE MATCH
- >= 0.80: HIGH CONFIDENCE
- >= 0.75: PROBABLE MATCH
- >= 0.65: POSSIBLE MATCH
- >= 0.60: WEAK SIGNAL
- < 0.60: DISCARD

Important: scheduler currently logs only when should_log is true. Alerts happen only when should_alert is true.

---

## 5) API Contract (Current)

From backend/main.py and frontend/src/utils/api.js:

- GET /api/health
- POST /api/person
- GET /api/person/{person_id}
- POST /api/person/{person_id}/photo
- GET /api/person/{person_id}/matches?limit=&offset=
- GET /api/person/{person_id}/timeline
- GET /api/person/{person_id}/map
- GET /api/person/{person_id}/stats
- POST /api/sighting/{person_id}
- GET /api/share/{token}
- POST /api/person/{person_id}/scan
- WS /ws/person/{person_id}

WebSocket events pushed by backend:
- connected
- pong
- new_match
- scan_complete
- radius_expanded

---

## 6) Data Contracts You Must Respect

Defined in backend/models.py:

- PersonProfile: scheduler/worker internal model
- SearchResult: worker output model before face verification
- PersonResponse, StatsResponse, MapData: frontend-facing response schemas

Critical contract for worker authors:
- image_url and/or image_data must be provided for face verification.
- If neither is provided, the result is ignored by scheduler.

---

## 7) Environment and Startup

### Backend local run
1. Create and activate virtual environment.
2. Install requirements.txt.
3. Copy env.example to .env and fill keys as needed.
4. Run: uvicorn backend.main:app --reload

### Frontend local run
1. cd frontend
2. npm install
3. npm run dev

### Full stack via Docker
- docker-compose up --build

Ports:
- Backend: 8000
- Frontend: 5173
- Postgres: 5432

---

## 8) Development Modes and Fallbacks

Face engine mode:
- If InsightFace loads: real detection + embeddings.
- If not: deterministic simulation mode is enabled.

Database mode:
- If DATABASE_URL is valid Postgres URL: asyncpg pool used.
- Else: SQLite file data/thirdeye.db is used.

Why this matters:
- Many "it works on my machine" issues come from different face engine modes.
- Schema and data encoding behavior differ slightly between Postgres and SQLite paths.

---

## 9) Worker Inventory (Current)

Enabled through scheduler _init_workers list:
- InstagramWorker
- TwitterWorker
- FacebookWorker
- RedditWorker
- YouTubeWorker
- GoogleImagesWorker
- NewsWorker
- PublicCamsWorker
- UsernameHuntWorker

Base class:
- backend/workers/base.py

Note:
- Worker can self-disable via credentials/dependency checks.
- Disabled workers are skipped and logged.

---

## 10) Common Change Playbooks for Models

### A) Add a new source worker
1. Create backend/workers/<source>.py extending BaseWorker.
2. Return list[SearchResult] with image_url or image_data.
3. Wire worker into SearchScheduler._init_workers.
4. Add required env vars to env.example.
5. Add dependency to requirements.txt if needed.
6. Validate by triggering POST /api/person/{id}/scan.

### B) Add a new dashboard metric
1. Extend response in backend/main.py stats endpoint.
2. Update StatsResponse in backend/models.py.
3. Render value in frontend/src/components/StatsPanel.jsx.
4. Ensure frontend API client remains compatible.

### C) Modify match thresholds
1. Change logic in backend/face_engine.py.
2. Confirm scheduler behavior in backend/scheduler.py still aligns.
3. Update alerting expectations in backend/alerts.py if needed.
4. Verify UI badges/cards still communicate levels correctly.

---

## 11) Known Sharp Edges

1. Scheduler expects profile.embeddings to contain bytes during processing; encoding format differences can break comparisons if changed carelessly.
2. run_web_crawl includes all enabled workers, including PublicCamsWorker, and run_camera_scan also executes PublicCamsWorker on its own interval.
3. Missing credentials do not always fail startup; they often disable channels/workers silently with logs.
4. Graph reports contain inferred edges; confirm behavior in source before refactoring.

---

## 12) Minimum Validation Before Merging

Backend sanity:
1. /api/health returns online.
2. Create person with at least one photo succeeds.
3. Manual scan endpoint returns "Scan triggered".
4. Matches endpoint remains schema-compatible.

Frontend sanity:
1. Landing page loads and person creation flow works.
2. Dashboard loads person, stats, map, timeline without console errors.
3. WebSocket connects and reconnect logic still works.

---

## 13) How Graphify Helps

Use graphify-out/GRAPH_REPORT.md to:
- Identify central abstractions quickly (PersonProfile, SearchResult, SearchScheduler).
- See cross-module coupling before large refactors.
- Spot thin/isolated areas that may need documentation or extraction verification.

Do not use Graphify as sole truth for behavior. Always verify in source files listed above.

---

## 14) If You Are an Autonomous Coding Model

Execution order that works reliably:
1. Read this file.
2. Read backend/main.py, backend/scheduler.py, backend/models.py.
3. Read frontend/src/utils/api.js and frontend/src/pages/Dashboard.jsx.
4. Make smallest safe change set.
5. Validate endpoints/flow affected by your change.
6. Update this file if architecture or contracts changed.

If unsure between docs and code, trust code.
