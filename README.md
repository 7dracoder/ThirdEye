# ThirdEye

ThirdEye is a missing-person intelligence system with a FastAPI backend, scheduled source workers, face-matching, and a live React dashboard.

This repository is optimized for autonomous coding agents as well as human contributors.

## What is implemented now

- Person profile creation with one or more reference photos
- Face embedding extraction on upload
- Scheduled search orchestration (web crawl, camera scan, radius checks)
- Multi-source worker framework with per-worker enable/disable behavior
- Match persistence, timeline persistence, and map payload generation
- Crowdsource sighting submission endpoint
- Email and SMS alert channels (when credentials are configured)
- Real-time dashboard updates over WebSocket

## Important reality checks

- Face engine falls back to deterministic simulation mode if InsightFace models are unavailable.
- Database falls back to SQLite when DATABASE_URL is missing or PostgreSQL connection fails.
- Several workers are credential-gated and auto-disable when required keys are not set.
- Some Graphify edges are inferred. Verify behavior in source code before refactoring.

## Quick start (local)

### 1) Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
uvicorn backend.main:app --reload
```

Backend runs at http://localhost:8000.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173.

## Full stack with Docker

```bash
docker-compose up --build
```

Ports:
- Backend: 8000
- Frontend: 5173
- PostgreSQL: 5432

## Documentation map

- [INDEX.md](INDEX.md): full documentation index and reading paths
- [SKILLS.md](SKILLS.md): model-first contributor guide and change playbooks
- [ARCHITECTURE.md](ARCHITECTURE.md): runtime architecture and data flow
- [MODEL_CONTEXT.md](MODEL_CONTEXT.md): single-file full context for autonomous models
- [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md): graph-level structure insights
- [frontend/README.md](frontend/README.md): frontend-specific implementation notes

## API surface (current)

- GET /api/health
- POST /api/person
- GET /api/person/{person_id}
- POST /api/person/{person_id}/photo
- GET /api/person/{person_id}/matches
- GET /api/person/{person_id}/timeline
- GET /api/person/{person_id}/map
- GET /api/person/{person_id}/stats
- POST /api/sighting/{person_id}
- GET /api/share/{token}
- POST /api/person/{person_id}/scan
- WS /ws/person/{person_id}

## Primary code entry points

- backend/main.py
- backend/scheduler.py
- backend/models.py
- backend/database.py
- backend/face_engine.py
- frontend/src/pages/Dashboard.jsx
- frontend/src/utils/api.js
