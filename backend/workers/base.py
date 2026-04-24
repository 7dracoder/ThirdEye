"""
ThirdEye — Base Worker Interface
All search workers must extend this class and implement the `search` method.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from backend.models import PersonProfile, SearchResult


class BaseWorker(ABC):
    """Abstract base class for all search workers."""

    name: str = "base"
    description: str = "Base worker"

    def __init__(self):
        self.logger = logging.getLogger(f"thirdeye.worker.{self.name}")
        self._enabled = True

    @abstractmethod
    async def search(self, person: PersonProfile) -> list[SearchResult]:
        """
        Search this source for the missing person.

        Args:
            person: PersonProfile with name, embeddings, location info

        Returns:
            List of SearchResult objects (pre-face-matching)
        """
        raise NotImplementedError

    async def safe_search(self, person: PersonProfile) -> list[SearchResult]:
        """Wrapper that catches all errors and returns empty list on failure."""
        if not self._enabled:
            self.logger.debug(f"{self.name} worker is disabled")
            return []

        try:
            self.logger.info(f"Starting {self.name} search for person {person.id}")
            results = await self.search(person)
            self.logger.info(f"{self.name} returned {len(results)} results")
            return results
        except Exception as e:
            self.logger.error(f"{self.name} search failed: {e}")
            return []

    def disable(self):
        """Disable this worker."""
        self._enabled = False

    def enable(self):
        """Enable this worker."""
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled
