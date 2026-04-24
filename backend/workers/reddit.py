"""
ThirdEye — Reddit Worker
Searches Reddit posts and comments using PRAW API.
"""

import os
from datetime import datetime, timezone

from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker


class RedditWorker(BaseWorker):
    name = "reddit"
    description = "Search Reddit posts and comments with images"

    def __init__(self):
        super().__init__()
        self._reddit = None
        client_id = os.getenv("REDDIT_CLIENT_ID", "")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")

        if client_id and client_secret:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=os.getenv("REDDIT_USER_AGENT", "ThirdEye/1.0"),
                )
            except ImportError:
                self.logger.warning("PRAW not installed. Reddit worker disabled.")
                self.disable()
        else:
            self.logger.info("Reddit API credentials not set. Reddit worker disabled.")
            self.disable()

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not self._reddit:
            return []

        results = []

        # Subreddits relevant to missing persons
        subreddits = [
            "MissingPersons", "missingpersons", "UnresolvedMysteries",
            "RBI", "HelpMeFind", "Missing411",
        ]

        # Add location-based subreddits
        if person.last_known_location:
            location_parts = person.last_known_location.replace(",", "").split()
            for part in location_parts[:2]:
                subreddits.append(part.lower())

        search_queries = []
        if person.name:
            search_queries.append(person.name)
            search_queries.append(f"missing {person.name}")

        for subreddit_name in subreddits[:6]:
            for query in search_queries[:2]:
                try:
                    subreddit = self._reddit.subreddit(subreddit_name)
                    for submission in subreddit.search(query, limit=10, sort="new"):
                        # Check if post has an image
                        image_url = None
                        if hasattr(submission, "url") and submission.url:
                            url = submission.url.lower()
                            if any(ext in url for ext in [".jpg", ".jpeg", ".png", ".gif"]):
                                image_url = submission.url
                            elif "imgur.com" in url and not url.endswith("/"):
                                image_url = submission.url + ".jpg"
                            elif hasattr(submission, "preview"):
                                try:
                                    image_url = submission.preview["images"][0]["source"]["url"]
                                except (KeyError, IndexError):
                                    pass

                        if image_url:
                            created_utc = datetime.fromtimestamp(
                                submission.created_utc, tz=timezone.utc
                            )
                            result = SearchResult(
                                source="reddit",
                                url=f"https://reddit.com{submission.permalink}",
                                image_url=image_url,
                                timestamp=created_utc,
                                raw_text=f"{submission.title}\n{submission.selftext[:500]}",
                            )
                            results.append(result)

                except Exception as e:
                    self.logger.debug(f"Reddit search error in r/{subreddit_name}: {e}")
                    continue

        return results
