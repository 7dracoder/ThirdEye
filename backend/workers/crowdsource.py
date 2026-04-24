"""
ThirdEye — Crowdsource Sighting Worker
Handles volunteer-submitted sighting photos and live camera mode.
"""

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class CrowdsourceWorker(BaseWorker):
    name = "crowdsource"
    description = "Process volunteer-submitted sighting photos"

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        # Crowdsource is event-driven, not scheduled
        # This method is called when a sighting is submitted via API
        return []

    async def process_sighting(self, image_data: bytes, location: str = None,
                                lat: float = None, lng: float = None) -> SearchResult:
        """Process a single crowdsourced sighting submission."""
        return SearchResult(
            source="crowdsource",
            location=location,
            lat=lat, lng=lng,
            image_data=image_data,
        )
