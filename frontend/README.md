# ThirdEye Frontend

Frontend for the ThirdEye dashboard, built with React and Vite.

## Purpose

The frontend provides:
- Profile creation flow (intake)
- Live dashboard with match feed
- Map and timeline views
- Crowdsource share-link experience
- Real-time updates over WebSocket

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Default dev URL: http://localhost:5173

Set API host with VITE_API_URL if backend is not on localhost:8000.

## Build and preview

```bash
npm run build
npm run preview
```

## Core files

- src/App.jsx: routes and navbar shell
- src/pages/Landing.jsx: onboarding and upload entry
- src/pages/Dashboard.jsx: primary app state and tab flow
- src/components/UploadForm.jsx: profile and photo submission
- src/components/MatchCard.jsx: match rendering
- src/components/MapView.jsx: Leaflet map rendering
- src/components/Timeline.jsx: ordered location history
- src/components/StatsPanel.jsx: high-level metrics
- src/components/ShareLink.jsx: share token UX
- src/hooks/useWebSocket.js: socket lifecycle and reconnect
- src/utils/api.js: REST contract and WS base URL

## API dependencies

The frontend expects these backend endpoints:
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

## Frontend state flow

Dashboard load sequence:
1. Load person, matches, stats, map data, timeline in parallel.
2. Subscribe to WebSocket for person-specific events.
3. On new_match or scan_complete event, reload dashboard datasets.

WebSocket behavior:
- reconnects automatically after close
- sends periodic ping every 30 seconds
- stores latest event and a rolling event history in hook state

## Contributor notes

- Keep API changes synchronized between backend/main.py and src/utils/api.js.
- Preserve backward compatibility for payload shapes consumed in Dashboard and components.
- Validate both desktop and mobile layouts after UI changes.
