"""
ThirdEye — Google Images Worker
Reverse image search via SerpAPI or direct scraping.
"""

import os
from datetime import datetime, timezone

import httpx

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class GoogleImagesWorker(BaseWorker):
    name = "google_images"
    description = "Google reverse image search and text-based image search"

    def __init__(self):
        super().__init__()
        self._serpapi_key = os.getenv("SERPAPI_KEY", "")
        if not self._serpapi_key:
            self.logger.info("SerpAPI key not set. Google Images worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._serpapi_key:
            return []

        results = []

        # Text-based Google Image search
        queries = []
        if person.name:
            queries.append(f'"{person.name}" face photo')
            queries.append(f'"{person.name}" missing person')
        if person.last_known_location and person.name:
            queries.append(f'"{person.name}" {person.last_known_location}')

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in queries[:3]:
                try:
                    response = await client.get(
                        "https://serpapi.com/search",
                        params={
                            "engine": "google_images",
                            "q": query,
                            "api_key": self._serpapi_key,
                            "num": 10,
                        },
                    )

                    if response.status_code != 200:
                        continue

                    data = response.json()
                    for img in data.get("images_results", []):
                        image_url = img.get("original") or img.get("thumbnail")
                        source_url = img.get("link", "")

                        if image_url:
                            result = SearchResult(
                                source="google_images",
                                url=source_url,
                                image_url=image_url,
                                raw_text=img.get("title", ""),
                            )
                            results.append(result)

                except Exception as e:
                    self.logger.debug(f"Google Images search error: {e}")
                    continue

            # Reverse image search if we have photos
            for photo_path in person.photos[:2]:
                try:
                    response = await client.get(
                        "https://serpapi.com/search",
                        params={
                            "engine": "google_reverse_image",
                            "image_url": photo_path,
                            "api_key": self._serpapi_key,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        for match in data.get("image_results", []):
                            image_url = match.get("original") or match.get("thumbnail")
                            if image_url:
                                result = SearchResult(
                                    source="google_reverse_image",
                                    url=match.get("link", ""),
                                    image_url=image_url,
                                    raw_text=match.get("title", ""),
                                )
                                results.append(result)

                except Exception as e:
                    self.logger.debug(f"Reverse image search error: {e}")

        return results
