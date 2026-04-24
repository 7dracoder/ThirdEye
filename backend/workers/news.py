"""
ThirdEye — News Worker
Searches news articles using GNews API for missing person mentions.
"""

import os
from datetime import datetime, timezone

import httpx

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class NewsWorker(BaseWorker):
    name = "news"
    description = "Search news articles and photos via GNews API"

    def __init__(self):
        super().__init__()
        self._api_key = os.getenv("GNEWS_API_KEY", "")
        if not self._api_key:
            self.logger.info("GNews API key not set. News worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._api_key:
            return []

        results = []
        queries = []
        if person.name:
            queries.append(f'"{person.name}" missing')
        if person.last_known_location:
            queries.append(f'missing person {person.last_known_location}')

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in queries[:2]:
                try:
                    resp = await client.get(
                        "https://gnews.io/api/v4/search",
                        params={"q": query, "token": self._api_key, "lang": "en", "max": 10},
                    )
                    if resp.status_code != 200:
                        continue
                    for article in resp.json().get("articles", []):
                        img = article.get("image")
                        if img:
                            ts = None
                            pub = article.get("publishedAt", "")
                            if pub:
                                try:
                                    ts = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                                except ValueError:
                                    pass
                            results.append(SearchResult(
                                source="news", url=article.get("url", ""),
                                image_url=img, timestamp=ts,
                                raw_text=f"{article.get('title','')}\n{article.get('description','')}",
                            ))
                except Exception as e:
                    self.logger.debug(f"News search error: {e}")
        return results
