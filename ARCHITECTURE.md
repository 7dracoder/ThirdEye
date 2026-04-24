# ThirdEye Architecture

This document describes the architecture as currently implemented in code.

## System boundaries

- Backend service: FastAPI application and scheduler
- Worker layer: asynchronous source connectors returning SearchResult objects
- Face layer: embedding extraction and similarity scoring
- Persistence layer: PostgreSQL with SQLite fallback
- Frontend app: React dashboard consuming REST and WebSocket streams

## Startup and lifecycle

Startup flow in backend/main.py:
1. Connect to database.
2. Initialize AlertSystem, RadiusManager, SearchScheduler.
3. Start scheduler jobs.
4. Serve REST + WebSocket endpoints.

Shutdown flow:
1. Stop scheduler.
2. Disconnect from database.

## Scheduler design

Scheduler implementation: backend/scheduler.py

Recurring jobs:
- run_web_crawl every SCAN_INTERVAL_HOURS (default 6)
- run_camera_scan every CAM_SCAN_INTERVAL_MINUTES (default 10)
- check_radius_expansions every 1 hour

Immediate jobs:
- trigger_immediate_scan(person_id) from POST /api/person/{person_id}/scan and after person creation

## Worker pipeline

Worker contract:
- Base class: backend/workers/base.py
- Method: async search(person: PersonProfile) -> list[SearchResult]
- Execution wrapper: safe_search catches exceptions and returns empty list on failure

Current worker set initialized by scheduler:
- InstagramWorker
- TwitterWorker
- FacebookWorker
- RedditWorker
- YouTubeWorker
- GoogleImagesWorker
- NewsWorker
- PublicCamsWorker
- UsernameHuntWorker

Note: workers may self-disable when dependencies or credentials are missing.

## Match processing pipeline

For each SearchResult in scheduler processing:
1. Require image_url or image_data.
2. Load candidate image bytes.
3. Extract candidate embedding.
4. Compare against all reference embeddings for person.
5. If score is below log threshold, discard.
6. Persist match record.
7. Persist location record if lat/lng exists.
8. Broadcast WebSocket new_match event.
9. If score is above alert threshold, dispatch alerts and optionally reset epicenter.

Threshold functions from backend/face_engine.py:
- should_log(score): score >= 0.65
- should_alert(score): score >= 0.75

## Data model

Core entities:
- persons
- matches
- locations
- alerts_sent
- crowdsource_sightings
- cameras

Schema source:
- database/schema.sql

Application model contracts:
- backend/models.py

## API and realtime contract

REST and WS implementation:
- backend/main.py
- frontend/src/utils/api.js

WebSocket events currently emitted by backend:
- connected
- pong
- new_match
- scan_complete
- radius_expanded

## Frontend architecture

- Router and shell: frontend/src/App.jsx
- Intake page: frontend/src/pages/Landing.jsx
- Dashboard: frontend/src/pages/Dashboard.jsx
- Data access: frontend/src/utils/api.js
- Realtime hook: frontend/src/hooks/useWebSocket.js
- Visual modules: frontend/src/components

## Operational fallbacks

Face fallback:
- If InsightFace load fails, face_engine enters deterministic simulation mode.

Database fallback:
- If PostgreSQL is unavailable or DATABASE_URL is absent/invalid, backend/database.py uses SQLite.

## Known implementation gaps vs aspirational product copy

The repository includes marketing copy that implies features not fully enforced in backend code.

Examples:
- Browser push alerts are described in copy but backend alerting currently implements email and SMS.
- Strong anti-abuse controls (for example strict crowdsource rate limiting) are not centrally enforced in backend/main.py.
- Some workers are structural placeholders due source-platform restrictions.

Treat source code as the final truth when planning modifications.
