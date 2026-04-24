"""
ThirdEye — FastAPI Main Application
REST API + WebSocket endpoints for the missing person intelligence system.
"""

import os
import json
import uuid
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from backend.database import db
from backend.face_engine import face_engine
from backend.alerts import AlertSystem
from backend.radius_manager import RadiusManager
from backend.scheduler import SearchScheduler
from backend.models import PersonCreate, PersonResponse, MatchResponse, SightingSubmit, StatsResponse, MapData

# ── Logging ──
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "true").lower() == "true" else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("thirdeye.main")

# ── Paths ──
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Services ──
alert_system = None
radius_manager = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global alert_system, radius_manager, scheduler

    # Startup
    await db.connect()
    alert_system = AlertSystem(db)
    radius_manager = RadiusManager(db)
    scheduler = SearchScheduler(db, face_engine, alert_system, radius_manager)
    scheduler.start()
    logger.info("👁️ ThirdEye system online")

    yield

    # Shutdown
    if scheduler:
        scheduler.stop()
    await db.disconnect()
    logger.info("👁️ ThirdEye system offline")


# ── App ──
app = FastAPI(
    title="ThirdEye — Missing Person Intelligence System",
    description="Upload one photo. ThirdEye hunts across the open internet, public cameras, and crowdsourced sightings.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ── Health Check ──

@app.get("/api/health")
async def health_check():
    return {"status": "online", "system": "ThirdEye", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Person Endpoints ──

@app.post("/api/person", response_model=PersonResponse)
async def create_person(
    name: str = Form(None),
    age: int = Form(None),
    gender: str = Form(None),
    description: str = Form(None),
    last_known_location: str = Form(None),
    last_known_lat: float = Form(None),
    last_known_lng: float = Form(None),
    contact_info: str = Form(None),
    photos: list[UploadFile] = File(default=[]),
):
    """Create a new missing person search profile."""
    saved_photos = []
    embeddings_bytes = []

    for photo in photos:
        if photo.filename:
            # Save photo
            ext = Path(photo.filename).suffix or ".jpg"
            filename = f"{uuid.uuid4()}{ext}"
            filepath = UPLOAD_DIR / filename
            content = await photo.read()
            filepath.write_bytes(content)
            saved_photos.append(f"/uploads/{filename}")

            # Extract face embedding
            embedding = face_engine.extract_embedding(content)
            if embedding is not None:
                import base64
                emb_bytes = face_engine.embedding_to_bytes(embedding)
                embeddings_bytes.append(base64.b64encode(emb_bytes).decode("utf-8"))

    person_id = await db.create_person(
        name=name, age=age, gender=gender, description=description,
        last_known_location=last_known_location,
        last_known_lat=last_known_lat, last_known_lng=last_known_lng,
        contact_info=contact_info, photos=saved_photos,
        embeddings=embeddings_bytes,
    )

    person = await db.get_person(person_id)
    total_matches = await db.get_match_count(person_id)

    # Trigger immediate scan in background
    if scheduler and embeddings_bytes:
        asyncio.create_task(scheduler.trigger_immediate_scan(person_id))

    return PersonResponse(**{**person, "total_matches": total_matches})


@app.get("/api/person/{person_id}", response_model=PersonResponse)
async def get_person(person_id: str):
    """Get person profile and search status."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    total_matches = await db.get_match_count(person_id)
    return PersonResponse(**{**person, "total_matches": total_matches})


@app.post("/api/person/{person_id}/photo")
async def add_photo(person_id: str, photo: UploadFile = File(...)):
    """Add a reference photo to an existing person profile."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    content = await photo.read()
    ext = Path(photo.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(content)

    photo_url = f"/uploads/{filename}"
    current_photos = person.get("photos", [])
    if isinstance(current_photos, str):
        current_photos = json.loads(current_photos)
    current_photos.append(photo_url)

    embedding = face_engine.extract_embedding(content)

    await db.update_person(person_id, photos=json.dumps(current_photos))

    return {"message": "Photo added", "photo_url": photo_url, "face_detected": embedding is not None}


# ── Match Endpoints ──

@app.get("/api/person/{person_id}/matches")
async def get_matches(person_id: str, limit: int = 50, offset: int = 0):
    """Get all matches for a person (paginated)."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    matches = await db.get_matches(person_id, limit=limit, offset=offset)
    total = await db.get_match_count(person_id)

    return {"matches": matches, "total": total, "limit": limit, "offset": offset}


# ── Timeline Endpoint ──

@app.get("/api/person/{person_id}/timeline")
async def get_timeline(person_id: str):
    """Get location timeline for movement tracking."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    timeline = await db.get_timeline(person_id)
    return {"timeline": timeline}


# ── Map Endpoint ──

@app.get("/api/person/{person_id}/map")
async def get_map_data(person_id: str):
    """Get map data: epicenter, radius, location pins, path."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    timeline = await db.get_timeline(person_id)
    matches = await db.get_matches(person_id, limit=100)

    # Build pins from matches with coordinates
    pins = []
    for m in matches:
        if m.get("lat") and m.get("lng"):
            pins.append({
                "lat": m["lat"], "lng": m["lng"],
                "source": m["source"], "confidence": m["similarity"],
                "label": m["confidence_label"], "timestamp": m.get("created_at"),
            })

    # Build path from timeline
    path = [{"lat": l["lat"], "lng": l["lng"], "timestamp": l["timestamp"]} for l in timeline]

    return MapData(
        epicenter={"lat": person.get("epicenter_lat"), "lng": person.get("epicenter_lng")}
        if person.get("epicenter_lat") else None,
        radius_miles=person.get("current_radius", 1.0),
        pins=pins,
        path=path,
    )


# ── Stats Endpoint ──

@app.get("/api/person/{person_id}/stats", response_model=StatsResponse)
async def get_stats(person_id: str):
    """Get dashboard stats for a person."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    total = await db.get_match_count(person_id)
    high = len(await db.fetchall(
        "SELECT id FROM matches WHERE person_id = $1 AND similarity >= 0.75", person_id
    ))

    created = person.get("created_at", "")
    hours_running = 0
    if created:
        try:
            start = datetime.fromisoformat(created)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            hours_running = (datetime.now(timezone.utc) - start).total_seconds() / 3600
        except ValueError:
            pass

    return StatsResponse(
        status=person.get("status", "active"),
        total_matches=total,
        high_confidence_matches=high,
        sources_checked=len([w for w in scheduler._workers if w.is_enabled]) if scheduler else 0,
        current_radius=person.get("current_radius", 1.0),
        time_running_hours=round(hours_running, 1),
        last_scan_at=person.get("last_scan_at"),
    )


# ── Crowdsource Endpoints ──

@app.post("/api/sighting/{person_id}")
async def submit_sighting(
    person_id: str,
    request: Request,
    photo: UploadFile = File(...),
    location: str = Form(None),
    lat: float = Form(None),
    lng: float = Form(None),
    description: str = Form(None),
):
    """Submit a crowdsourced sighting."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    content = await photo.read()
    ext = Path(photo.filename).suffix or ".jpg"
    filename = f"sighting_{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(content)

    # Face match check
    similarity = 0.0
    confidence_label = "DISCARD"
    candidate = face_engine.extract_embedding(content)
    if candidate is not None:
        ref_embeddings = []
        raw_embeddings = person.get("embeddings", [])
        if isinstance(raw_embeddings, str):
            raw_embeddings = json.loads(raw_embeddings)
        import base64
        for emb in raw_embeddings:
            if isinstance(emb, str):
                emb = base64.b64decode(emb)
            if isinstance(emb, bytes):
                ref_embeddings.append(face_engine.bytes_to_embedding(emb))
        if ref_embeddings:
            similarity, confidence_label = face_engine.compare_faces(ref_embeddings, candidate)

    status = "accepted" if similarity >= 0.75 else "review" if similarity >= 0.65 else "rejected"
    submitter_ip = request.client.host if request.client else None

    sighting_id = await db.create_sighting(
        person_id=person_id,
        share_token=person.get("share_token", ""),
        image_path=f"/uploads/{filename}",
        location=location, lat=lat, lng=lng,
        description=description, similarity=similarity,
        confidence_label=confidence_label, status=status,
        submitter_ip=submitter_ip,
    )

    return {"sighting_id": sighting_id, "status": status, "similarity": similarity, "label": confidence_label}


@app.get("/api/share/{token}")
async def get_share_info(token: str):
    """Get public info for crowdsource sighting form."""
    person = await db.get_person_by_token(token)
    if not person:
        raise HTTPException(status_code=404, detail="Invalid share link")

    return {
        "person_id": person["id"],
        "name": person.get("name", "Unknown"),
        "description": person.get("description", ""),
        "last_known_location": person.get("last_known_location", ""),
    }


# ── WebSocket ──

@app.websocket("/ws/person/{person_id}")
async def websocket_endpoint(websocket: WebSocket, person_id: str):
    """WebSocket for live dashboard updates."""
    await websocket.accept()

    if scheduler:
        scheduler.register_ws(person_id, websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "connected",
            "data": {"person_id": person_id, "timestamp": datetime.now(timezone.utc).isoformat()}
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong
            if data == "ping":
                await websocket.send_json({"event": "pong"})

    except WebSocketDisconnect:
        if scheduler:
            scheduler.unregister_ws(person_id, websocket)


# ── Scan Trigger ──

@app.post("/api/person/{person_id}/scan")
async def trigger_scan(person_id: str):
    """Manually trigger an immediate scan."""
    person = await db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if scheduler:
        asyncio.create_task(scheduler.trigger_immediate_scan(person_id))
        return {"message": "Scan triggered", "person_id": person_id}

    raise HTTPException(status_code=503, detail="Scheduler not available")
