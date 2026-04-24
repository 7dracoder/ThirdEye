"""
ThirdEye — Twitter/X Worker
Searches public Twitter/X posts using snscrape.
"""

from datetime import datetime, timezone

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class TwitterWorker(BaseWorker):
    name = "twitter"
    description = "Search public Twitter/X posts and media"

    def __init__(self):
        super().__init__()
        self._available = False
        try:
            import snscrape.modules.twitter as sntwitter
            self._available = True
        except ImportError:
            self.logger.warning("snscrape not installed. Twitter worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._available:
            return []

        results = []

        try:
            import snscrape.modules.twitter as sntwitter

            # Build search queries
            queries = []
            if person.name:
                queries.append(f'"{person.name}" filter:images')
                queries.append(f'"{person.name}" missing')
            if person.last_known_location:
                if person.name:
                    queries.append(f'"{person.name}" near:"{person.last_known_location}"')

            for query in queries[:3]:
                try:
                    scraper = sntwitter.TwitterSearchScraper(query)
                    for i, tweet in enumerate(scraper.get_items()):
                        if i >= 20:
                            break

                        # Check for media (images)
                        image_url = None
                        if hasattr(tweet, "media") and tweet.media:
                            for media in tweet.media:
                                if hasattr(media, "fullUrl"):
                                    image_url = media.fullUrl
                                    break
                                elif hasattr(media, "previewUrl"):
                                    image_url = media.previewUrl
                                    break

                        if image_url:
                            result = SearchResult(
                                source="twitter",
                                url=tweet.url,
                                image_url=image_url,
                                timestamp=tweet.date.replace(tzinfo=timezone.utc) if tweet.date else None,
                                location=str(tweet.place) if hasattr(tweet, "place") and tweet.place else None,
                                lat=tweet.coordinates.latitude if hasattr(tweet, "coordinates") and tweet.coordinates else None,
                                lng=tweet.coordinates.longitude if hasattr(tweet, "coordinates") and tweet.coordinates else None,
                                raw_text=tweet.rawContent if hasattr(tweet, "rawContent") else "",
                            )
                            results.append(result)

                except Exception as e:
                    self.logger.debug(f"Twitter search error for query '{query}': {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Twitter worker error: {e}")

        return results
