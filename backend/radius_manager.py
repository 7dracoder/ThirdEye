"""
ThirdEye — Expanding Search Radius Manager
Automatically expands geographic search area over time.
Resets epicenter when a new confirmed match is found.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("thirdeye.radius")

# Expansion schedule from env
RADIUS_1MI_HOURS = int(os.getenv("RADIUS_1MI_HOURS", "6"))
RADIUS_5MI_HOURS = int(os.getenv("RADIUS_5MI_HOURS", "12"))
RADIUS_20MI_HOURS = int(os.getenv("RADIUS_20MI_HOURS", "24"))
RADIUS_CITY_DAYS = int(os.getenv("RADIUS_CITY_DAYS", "7"))

EXPANSION_SCHEDULE = [
    (timedelta(hours=0), 1.0, "1 mile"),
    (timedelta(hours=RADIUS_1MI_HOURS), 5.0, "5 miles"),
    (timedelta(hours=RADIUS_5MI_HOURS), 20.0, "20 miles"),
    (timedelta(hours=RADIUS_20MI_HOURS), 50.0, "Full city"),
    (timedelta(days=RADIUS_CITY_DAYS), 100.0, "Neighboring cities"),
    (timedelta(days=14), 250.0, "Full state"),
]


class RadiusManager:
    """Manages the expanding search radius for a person."""

    def __init__(self, db):
        self.db = db

    async def check_expansion(self, person_id: str) -> Optional[dict]:
        """Check if the radius should be expanded. Returns new state if changed."""
        person = await self.db.get_person(person_id)
        if not person or person.get("status") != "active":
            return None

        created_at = person.get("created_at", "")
        if not created_at:
            return None

        # Parse creation time
        if isinstance(created_at, str):
            try:
                start_time = datetime.fromisoformat(created_at)
            except ValueError:
                return None
        else:
            start_time = created_at

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        elapsed = datetime.now(timezone.utc) - start_time
        current_radius = person.get("current_radius", 1.0)

        # Find the appropriate radius for elapsed time
        new_radius = 1.0
        new_label = "1 mile"
        for threshold, radius, label in EXPANSION_SCHEDULE:
            if elapsed >= threshold:
                new_radius = radius
                new_label = label

        if new_radius > current_radius:
            await self.db.update_person(person_id, current_radius=new_radius)
            logger.info(f"Radius expanded for {person_id}: {current_radius} → {new_radius} miles ({new_label})")

            next_expansion = self._get_next_expansion(elapsed)

            return {
                "person_id": person_id,
                "previous_radius": current_radius,
                "new_radius": new_radius,
                "label": new_label,
                "elapsed_hours": elapsed.total_seconds() / 3600,
                "next_expansion_at": next_expansion,
            }

        return None

    async def reset_epicenter(self, person_id: str, lat: float, lng: float):
        """Reset search epicenter after a confirmed match."""
        await self.db.update_person(
            person_id,
            epicenter_lat=lat,
            epicenter_lng=lng,
            current_radius=1.0,
        )
        logger.info(f"Epicenter reset for {person_id} to ({lat}, {lng}), radius back to 1 mile")

    def _get_next_expansion(self, elapsed: timedelta) -> Optional[str]:
        """Calculate when the next expansion will occur."""
        for threshold, radius, label in EXPANSION_SCHEDULE:
            if elapsed < threshold:
                return threshold.total_seconds() / 3600
        return None

    @staticmethod
    def get_radius_info(current_radius: float) -> dict:
        """Get human-readable info about the current radius."""
        for _, radius, label in EXPANSION_SCHEDULE:
            if current_radius <= radius:
                return {"radius_miles": current_radius, "label": label}
        return {"radius_miles": current_radius, "label": "Maximum range"}
