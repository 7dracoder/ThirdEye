"""
ThirdEye — Username Hunt Worker
Social account discovery across platforms using username variations.
"""

import httpx
from backend.models import PersonProfile, SearchResult
from backend.workers.base import BaseWorker

# Platforms to check for username existence
PLATFORMS = [
    {"name": "Instagram", "url": "https://www.instagram.com/{}/", "err": 404},
    {"name": "Twitter", "url": "https://twitter.com/{}", "err": 404},
    {"name": "Facebook", "url": "https://www.facebook.com/{}", "err": 404},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}", "err": 404},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "err": 404},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/", "err": 404},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "err": 404},
    {"name": "GitHub", "url": "https://github.com/{}", "err": 404},
    {"name": "Flickr", "url": "https://www.flickr.com/people/{}", "err": 404},
]


class UsernameHuntWorker(BaseWorker):
    name = "username_hunt"
    description = "Discover social media accounts by username variations"

    async def search(self, person: PersonProfile) -> list[SearchResult]:
        if not person.name:
            return []

        results = []
        usernames = self._generate_usernames(person.name)

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for username in usernames[:5]:
                for platform in PLATFORMS:
                    try:
                        url = platform["url"].format(username)
                        resp = await client.get(url, headers={
                            "User-Agent": "Mozilla/5.0 (compatible; ThirdEye/1.0)"
                        })
                        if resp.status_code == 200:
                            results.append(SearchResult(
                                source=f"username_{platform['name'].lower()}",
                                url=url,
                                raw_text=f"Account found: @{username} on {platform['name']}",
                            ))
                    except Exception:
                        continue

        return results

    @staticmethod
    def _generate_usernames(name: str) -> list[str]:
        """Generate common username variations from a person's name."""
        parts = name.lower().split()
        if len(parts) < 2:
            return [parts[0]] if parts else []
        first, last = parts[0], parts[-1]
        return [
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
        ]
