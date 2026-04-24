"""
ThirdEye — Public Camera Processor
Pulls live frames from public camera streams and runs face detection.
Sources: NYC DOT, 511NY/NJ, Shodan, EarthCam.
"""

import os
from datetime import datetime, timezone
import httpx
from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class PublicCamsWorker(BaseWorker):
    name = "public_cams"
    description = "Monitor public traffic and IP cameras for face matches"

    # NYC DOT Camera API
    NYC_DOT_API = "https://webcams.nyctmc.org/api/cameras"
    SHODAN_API = "https://api.shodan.io"

    def __init__(self):
        super().__init__()
        self._shodan_key = os.getenv("SHODAN_API_KEY", "")

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        results = []
        results.extend(await self._search_nyc_dot(person))
        if self._shodan_key:
            results.extend(await self._search_shodan(person))
        return results

    async def _search_nyc_dot(self, person: PersonProfile) -> list[SearchResult]:
        """Search NYC DOT traffic cameras."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.NYC_DOT_API)
                if resp.status_code != 200:
                    return results
                cameras = resp.json() if isinstance(resp.json(), list) else resp.json().get("cameras", [])
                # Filter by radius if epicenter is set
                for cam in cameras[:50]:
                    img_url = cam.get("imageUrl") or cam.get("url", "")
                    if img_url:
                        results.append(SearchResult(
                            source="nyc_dot_cam",
                            url=img_url, image_url=img_url,
                            timestamp=datetime.now(timezone.utc),
                            location=cam.get("name", "NYC DOT Camera"),
                            lat=cam.get("latitude"), lng=cam.get("longitude"),
                        ))
        except Exception as e:
            self.logger.debug(f"NYC DOT error: {e}")
        return results

    async def _search_shodan(self, person: PersonProfile) -> list[SearchResult]:
        """Search Shodan for open IP cameras near the search area."""
        results = []
        try:
            query = "webcam"
            if person.last_known_location:
                query += f" city:{person.last_known_location.split(',')[0].strip()}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.SHODAN_API}/shodan/host/search",
                    params={"key": self._shodan_key, "query": query, "facets": "country"},
                )
                if resp.status_code == 200:
                    for match in resp.json().get("matches", [])[:20]:
                        ip = match.get("ip_str", "")
                        port = match.get("port", 80)
                        loc = match.get("location", {})
                        results.append(SearchResult(
                            source="shodan_cam",
                            url=f"http://{ip}:{port}",
                            image_url=f"http://{ip}:{port}/snapshot.jpg",
                            timestamp=datetime.now(timezone.utc),
                            location=f"{loc.get('city','')}, {loc.get('country_name','')}",
                            lat=loc.get("latitude"), lng=loc.get("longitude"),
                        ))
        except Exception as e:
            self.logger.debug(f"Shodan error: {e}")
        return results
