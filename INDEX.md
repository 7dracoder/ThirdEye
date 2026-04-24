# ThirdEye Documentation Index

This index is the canonical navigation map for contributors and coding agents.

## Start here

1. [MODEL_CONTEXT.md](MODEL_CONTEXT.md)
2. [SKILLS.md](SKILLS.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md)
4. [README.md](README.md)

## By purpose

### Full-context onboarding
- [MODEL_CONTEXT.md](MODEL_CONTEXT.md): end-to-end context in one file
- [SKILLS.md](SKILLS.md): practical contributor guide and safe change playbooks

### Architecture and runtime behavior
- [ARCHITECTURE.md](ARCHITECTURE.md): startup, scheduler flow, worker processing, data flow
- [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md): graph-level topology and hubs

### Setup and environment
- [README.md](README.md): local and Docker quick start
- [env.example](env.example): all environment variables used by the app
- [docker-compose.yml](docker-compose.yml): local stack orchestration
- [requirements.txt](requirements.txt): backend dependencies
- [frontend/package.json](frontend/package.json): frontend dependencies and scripts

### Database
- [database/schema.sql](database/schema.sql): PostgreSQL schema
- [backend/database.py](backend/database.py): Postgres/SQLite abstraction

### Backend implementation
- [backend/main.py](backend/main.py): API and WebSocket contract
- [backend/scheduler.py](backend/scheduler.py): orchestration and match pipeline
- [backend/models.py](backend/models.py): data contracts
- [backend/face_engine.py](backend/face_engine.py): face matching logic
- [backend/radius_manager.py](backend/radius_manager.py): radius progression behavior
- [backend/alerts.py](backend/alerts.py): alerting behavior
- [backend/workers/base.py](backend/workers/base.py): worker interface
- [backend/workers](backend/workers): source workers

### Frontend implementation
- [frontend/README.md](frontend/README.md): frontend architecture and runbook
- [frontend/src/pages/Landing.jsx](frontend/src/pages/Landing.jsx): intake flow
- [frontend/src/pages/Dashboard.jsx](frontend/src/pages/Dashboard.jsx): live dashboard state flow
- [frontend/src/hooks/useWebSocket.js](frontend/src/hooks/useWebSocket.js): live updates and reconnect
- [frontend/src/utils/api.js](frontend/src/utils/api.js): frontend API client

## Recommended reading order for coding models

1. [MODEL_CONTEXT.md](MODEL_CONTEXT.md)
2. [SKILLS.md](SKILLS.md)
3. [backend/main.py](backend/main.py)
4. [backend/scheduler.py](backend/scheduler.py)
5. [backend/models.py](backend/models.py)
6. [frontend/src/utils/api.js](frontend/src/utils/api.js)
7. [frontend/src/pages/Dashboard.jsx](frontend/src/pages/Dashboard.jsx)
