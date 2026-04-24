"""
ThirdEye — Instagram Worker
Searches public Instagram profiles and posts using Instaloader.
"""

import os
from datetime import datetime, timezone

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class InstagramWorker(BaseWorker):
    name = "instagram"
    description = "Search public Instagram profiles and posts"

    def __init__(self):
        super().__init__()
        self._loader = None
        try:
            import instaloader
            self._loader = instaloader.Instaloader(
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=True,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )
        except ImportError:
            self.logger.warning("Instaloader not installed. Instagram worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._loader:
            return []

        results = []

        # Search by name/username if available
        search_terms = []
        if person.name:
            search_terms.append(person.name)
            # Also try username variations
            search_terms.append(person.name.lower().replace(" ", ""))
            search_terms.append(person.name.lower().replace(" ", "_"))

        for term in search_terms[:3]:  # Limit to avoid rate limits
            try:
                import instaloader
                profile_results = instaloader.TopSearchResults(self._loader.context, term)

                for profile in list(profile_results.get_profiles())[:5]:
                    try:
                        # Get recent posts with images
                        for post in profile.get_posts():
                            if post.typename == "GraphImage" and post.url:
                                result = SearchResult(
                                    source="instagram",
                                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                                    image_url=post.url,
                                    timestamp=post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else None,
                                    location=str(post.location) if post.location else None,
                                    lat=post.location.lat if post.location and hasattr(post.location, "lat") else None,
                                    lng=post.location.lng if post.location and hasattr(post.location, "lng") else None,
                                    raw_text=post.caption or "",
                                )
                                results.append(result)

                            # Limit posts per profile
                            if len(results) >= 20:
                                break

                    except Exception as e:
                        self.logger.debug(f"Error processing profile {profile.username}: {e}")
                        continue

            except Exception as e:
                self.logger.debug(f"Instagram search error for '{term}': {e}")
                continue

        return results
