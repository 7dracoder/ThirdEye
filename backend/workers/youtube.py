"""
ThirdEye — YouTube Worker
Searches YouTube for video thumbnails and metadata via YouTube Data API v3.
"""

import os
from datetime import datetime, timezone

import httpx

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class YouTubeWorker(BaseWorker):
    name = "youtube"
    description = "Search YouTube videos for thumbnails and mentions"

    def __init__(self):
        super().__init__()
        self._api_key = os.getenv("YOUTUBE_API_KEY", "")
        if not self._api_key:
            self.logger.info("YouTube API key not set. YouTube worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._api_key:
            return []

        results = []
        queries = []

        if person.name:
            queries.append(f'"{person.name}" missing person')
            queries.append(f'"{person.name}"')
        if person.last_known_location and person.name:
            queries.append(f'"{person.name}" {person.last_known_location}')

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in queries[:3]:
                try:
                    response = await client.get(
                        "https://www.googleapis.com/youtube/v3/search",
                        params={
                            "part": "snippet",
                            "q": query,
                            "type": "video",
                            "maxResults": 10,
                            "key": self._api_key,
                            "order": "date",
                        },
                    )

                    if response.status_code != 200:
                        self.logger.debug(f"YouTube API error: {response.status_code}")
                        continue

                    data = response.json()
                    for item in data.get("items", []):
                        snippet = item.get("snippet", {})
                        video_id = item.get("id", {}).get("videoId", "")

                        # Get the highest quality thumbnail
                        thumbnails = snippet.get("thumbnails", {})
                        image_url = (
                            thumbnails.get("maxres", {}).get("url")
                            or thumbnails.get("high", {}).get("url")
                            or thumbnails.get("medium", {}).get("url")
                            or thumbnails.get("default", {}).get("url")
                        )

                        if image_url and video_id:
                            published = snippet.get("publishedAt", "")
                            timestamp = None
                            if published:
                                try:
                                    timestamp = datetime.fromisoformat(
                                        published.replace("Z", "+00:00")
                                    )
                                except ValueError:
                                    pass

                            result = SearchResult(
                                source="youtube",
                                url=f"https://www.youtube.com/watch?v={video_id}",
                                image_url=image_url,
                                timestamp=timestamp,
                                raw_text=f"{snippet.get('title', '')}\n{snippet.get('description', '')}",
                            )
                            results.append(result)

                except Exception as e:
                    self.logger.debug(f"YouTube search error: {e}")
                    continue

        return results
