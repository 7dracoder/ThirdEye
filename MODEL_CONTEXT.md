# MODEL_CONTEXT

Use this file as the fastest full-context handoff for autonomous coding models.

## 1) Objective

ThirdEye ingests reference photos for a person, scans multiple public data sources on a schedule, scores candidate images using face embeddings, stores possible matches, and pushes live updates to a React dashboard.

## 2) Canonical entry points

Read these in order:
1. SKILLS.md
2. backend/main.py
3. backend/scheduler.py
4. backend/models.py
5. backend/database.py
6. frontend/src/utils/api.js
7. frontend/src/pages/Dashboard.jsx

## 3) Primary runtime flow

Person creation:
1. POST /api/person with photos and optional metadata.
2. Backend stores uploaded images under uploads/.
3. Face engine extracts reference embeddings.
4. Person row is created with photos and embeddings.
5. Immediate scan may be triggered when embeddings exist.

Scheduled processing:
1. Scheduler fetches active persons.
2. Enabled workers run in parallel and return SearchResult objects.
3. Scheduler resolves candidate images and computes similarity.
4. Matches at score >= 0.65 are persisted.
5. Matches at score >= 0.75 trigger alerts.
6. WebSocket events notify active dashboards.

## 4) Contracts that cannot be broken

- Worker output type: list[SearchResult]
- SearchResult must include image_url or image_data for face scoring
- PersonProfile fields are filtered by model_fields before worker use
- Frontend expects response envelopes from api.js calls as implemented today

## 5) Worker and scheduler realities

- Workers may disable themselves at runtime if credentials/dependencies are missing.
- Public camera worker runs in both web crawl set and camera scan job path.
- Scheduler-safe behavior is fail-soft: worker errors are swallowed by safe_search and do not abort global scan.

## 6) Storage realities

- PostgreSQL is preferred when DATABASE_URL is valid.
- SQLite fallback path: data/thirdeye.db
- Schema source of truth: database/schema.sql

## 7) Face engine realities

- Preferred mode: InsightFace model runtime.
- Fallback mode: deterministic hash-based simulation embeddings.
- Similarity labels and alert/log thresholds are defined in backend/face_engine.py.

## 8) Realtime contract

WebSocket endpoint: /ws/person/{person_id}

Observed event names:
- connected
- pong
- new_match
- scan_complete
- radius_expanded

## 9) Known drift risks

- Marketing copy may include aspirational capabilities not fully enforced in backend logic.
- Graphify includes inferred edges; do not treat all inferred links as hard dependencies.
- Environment variable examples may omit some optional worker-specific keys.

## 10) Safe change protocol for autonomous models

1. Find the relevant contract in models.py and api.js first.
2. Make minimal changes in backend and frontend together if payload shape changes.
3. Preserve scheduler fail-soft behavior unless intentionally changing reliability policy.
4. Re-check docs: SKILLS.md, ARCHITECTURE.md, README.md, INDEX.md after behavior changes.
5. Prefer code truth over historical markdown statements.
