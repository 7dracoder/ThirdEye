"""
ThirdEye — Background Scheduler
Orchestrates all search workers on a schedule using APScheduler.
"""

import asyncio
import logging
from datetime import datetime, timezone
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("thirdeye.scheduler")

SCAN_INTERVAL_HOURS = int(os.getenv("SCAN_INTERVAL_HOURS", "6"))
CAM_SCAN_INTERVAL_MINUTES = int(os.getenv("CAM_SCAN_INTERVAL_MINUTES", "10"))


class SearchScheduler:
    """Manages background search jobs for all active persons."""

    def __init__(self, db, face_engine, alert_system, radius_manager):
        self.db = db
        self.face_engine = face_engine
        self.alert_system = alert_system
        self.radius_manager = radius_manager
        self._scheduler = None
        self._workers = []
        self._ws_connections = {}  # person_id -> set of websocket connections
        self._init_workers()

    def _init_workers(self):
        """Initialize all search workers."""
        from backend.workers.instagram import InstagramWorker
        from backend.workers.twitter import TwitterWorker
        from backend.workers.facebook import FacebookWorker
        from backend.workers.reddit import RedditWorker
        from backend.workers.youtube import YouTubeWorker
        from backend.workers.google_images import GoogleImagesWorker
        from backend.workers.news import NewsWorker
        from backend.workers.public_cams import PublicCamsWorker
        from backend.workers.username_hunt import UsernameHuntWorker

        self._workers = [
            InstagramWorker(),
            TwitterWorker(),
            FacebookWorker(),
            RedditWorker(),
            YouTubeWorker(),
            GoogleImagesWorker(),
            NewsWorker(),
            PublicCamsWorker(),
            UsernameHuntWorker(),
        ]

        enabled = [w for w in self._workers if w.is_enabled]
        disabled = [w for w in self._workers if not w.is_enabled]
        logger.info(f"Workers initialized: {len(enabled)} enabled, {len(disabled)} disabled")
        for w in disabled:
            logger.info(f"  Disabled: {w.name} — missing credentials or dependencies")

    def start(self):
        """Start the APScheduler."""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler

            self._scheduler = AsyncIOScheduler()

            # Web crawl: every N hours
            self._scheduler.add_job(
                self.run_web_crawl, "interval",
                hours=SCAN_INTERVAL_HOURS, id="web_crawl",
                next_run_time=None,  # Don't run immediately
            )

            # Camera scan: every N minutes
            self._scheduler.add_job(
                self.run_camera_scan, "interval",
                minutes=CAM_SCAN_INTERVAL_MINUTES, id="camera_scan",
                next_run_time=None,
            )

            # Radius expansion check: every hour
            self._scheduler.add_job(
                self.check_radius_expansions, "interval",
                hours=1, id="radius_check",
                next_run_time=None,
            )

            self._scheduler.start()
            logger.info("Scheduler started")

        except ImportError:
            logger.warning("APScheduler not installed. Background jobs disabled.")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    async def run_web_crawl(self):
        """Run all web crawl workers for all active persons."""
        persons = await self.db.fetchall(
            "SELECT * FROM persons WHERE status = $1", "active"
        )

        for person_data in persons:
            await self._search_person(person_data)

    async def run_camera_scan(self):
        """Run camera processor for all active persons."""
        from backend.workers.public_cams import PublicCamsWorker

        cam_worker = next((w for w in self._workers if isinstance(w, PublicCamsWorker)), None)
        if not cam_worker:
            return

        persons = await self.db.fetchall(
            "SELECT * FROM persons WHERE status = $1", "active"
        )

        for person_data in persons:
            from backend.models import PersonProfile
            profile = PersonProfile(**{
                k: v for k, v in person_data.items()
                if k in PersonProfile.model_fields
            })
            results = await cam_worker.safe_search(profile)
            await self._process_results(profile, results, "camera_scan")

    async def check_radius_expansions(self):
        """Check if any person's search radius should expand."""
        persons = await self.db.fetchall(
            "SELECT id FROM persons WHERE status = $1", "active"
        )

        for person_data in persons:
            result = await self.radius_manager.check_expansion(person_data["id"])
            if result:
                await self._broadcast_ws(person_data["id"], {
                    "event": "radius_expanded",
                    "data": result,
                })

    async def _search_person(self, person_data: dict):
        """Run all workers for a single person."""
        from backend.models import PersonProfile

        profile = PersonProfile(**{
            k: v for k, v in person_data.items()
            if k in PersonProfile.model_fields
        })

        # Run all workers in parallel
        tasks = [w.safe_search(profile) for w in self._workers if w.is_enabled]
        all_results = await asyncio.gather(*tasks)

        total_results = []
        for results in all_results:
            total_results.extend(results)

        await self._process_results(profile, total_results, "web_crawl")

        # Update last scan timestamp
        await self.db.update_person(
            profile.id,
            last_scan_at=datetime.now(timezone.utc).isoformat()
        )

        await self._broadcast_ws(profile.id, {
            "event": "scan_complete",
            "data": {
                "sources_checked": len([w for w in self._workers if w.is_enabled]),
                "results_found": len(total_results),
            }
        })

    async def _process_results(self, profile, results, scan_type):
        """Process search results: face match, save, alert."""
        from backend.face_engine import should_alert, should_log

        matches_found = 0

        for result in results:
            if not result.image_url and not result.image_data:
                continue

            # Download image and extract face embedding
            candidate_embedding = None
            if result.image_data:
                candidate_embedding = self.face_engine.extract_embedding(result.image_data)
            elif result.image_url:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.get(result.image_url)
                        if resp.status_code == 200:
                            candidate_embedding = self.face_engine.extract_embedding(resp.content)
                except Exception:
                    continue

            if candidate_embedding is None:
                continue

            # Compare against reference embeddings
            ref_embeddings = []
            for emb_data in profile.embeddings:
                if isinstance(emb_data, bytes):
                    ref_embeddings.append(self.face_engine.bytes_to_embedding(emb_data))

            if not ref_embeddings:
                continue

            score, label = self.face_engine.compare_faces(ref_embeddings, candidate_embedding)

            if not should_log(score):
                continue

            # Save match
            match_id = await self.db.create_match(
                person_id=profile.id,
                source=result.source,
                url=result.url,
                image_url=result.image_url,
                similarity=score,
                confidence_label=label,
                location=result.location,
                lat=result.lat, lng=result.lng,
                raw_text=result.raw_text,
            )
            matches_found += 1

            # Save location if available
            if result.lat and result.lng:
                await self.db.create_location(
                    person_id=profile.id,
                    match_id=match_id,
                    location=result.location or "Unknown",
                    lat=result.lat, lng=result.lng,
                    source=result.source,
                    confidence=score,
                    timestamp=result.timestamp.isoformat() if result.timestamp else datetime.now(timezone.utc).isoformat(),
                )

            # Broadcast to WebSocket
            await self._broadcast_ws(profile.id, {
                "event": "new_match",
                "data": {
                    "match_id": match_id,
                    "source": result.source,
                    "similarity": score,
                    "label": label,
                    "location": result.location,
                    "image_url": result.image_url,
                }
            })

            # Send alert if high confidence
            if should_alert(score):
                await self.alert_system.send_alert(profile.id, {
                    "confidence": score,
                    "label": label,
                    "source": result.source,
                    "location": result.location,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "image_url": result.image_url,
                    "post_url": result.url,
                    "lat": result.lat, "lng": result.lng,
                    "match_id": match_id,
                })

                # Reset epicenter if we have coordinates
                if result.lat and result.lng:
                    await self.radius_manager.reset_epicenter(
                        profile.id, result.lat, result.lng
                    )

    def register_ws(self, person_id: str, ws):
        """Register a WebSocket connection for live updates."""
        if person_id not in self._ws_connections:
            self._ws_connections[person_id] = set()
        self._ws_connections[person_id].add(ws)

    def unregister_ws(self, person_id: str, ws):
        """Remove a WebSocket connection."""
        if person_id in self._ws_connections:
            self._ws_connections[person_id].discard(ws)

    async def _broadcast_ws(self, person_id: str, message: dict):
        """Broadcast a message to all WebSocket connections for a person."""
        import json
        connections = self._ws_connections.get(person_id, set())
        dead = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            connections.discard(ws)

    async def trigger_immediate_scan(self, person_id: str):
        """Trigger an immediate scan for a specific person."""
        person_data = await self.db.get_person(person_id)
        if person_data:
            await self._search_person(person_data)
