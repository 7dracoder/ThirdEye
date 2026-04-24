"""
ThirdEye — Facebook Worker
Searches public Facebook posts and photos via public Graph API endpoints.
"""

import os

import httpx

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class FacebookWorker(BaseWorker):
    name = "facebook"
    description = "Search public Facebook posts and photos"

    def __init__(self):
        super().__init__()
        # Facebook public search is very limited without auth
        # This worker serves as a structural placeholder

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        results = []

        # Facebook public search is extremely restricted
        # This worker would need a Facebook App Token for Graph API
        # For now, it searches public pages mentioning missing persons

        search_terms = []
        if person.name:
            search_terms.append(person.name)
        if person.last_known_location:
            search_terms.append(f"missing person {person.last_known_location}")

        for term in search_terms[:2]:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Search public Facebook posts via web scraping fallback
                    response = await client.get(
                        "https://www.facebook.com/search/posts/",
                        params={"q": term},
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; ThirdEye/1.0)"
                        },
                        follow_redirects=True,
                    )

                    if response.status_code == 200:
                        # Parse results would go here
                        # Facebook heavily restricts automated access
                        self.logger.debug(f"Facebook search completed for '{term}'")

            except Exception as e:
                self.logger.debug(f"Facebook search error: {e}")
                continue

        return results
