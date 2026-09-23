from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from .models import Offer, SearchSession, Settings, SyncProgress


class OfferRepository(ABC):
    @abstractmethod
    async def add(self, offer: Offer) -> None:
        pass

    @abstractmethod
    async def add_batch(self, offers: list[Offer]) -> None:
        pass

    @abstractmethod
    async def get_by_fingerprint(self, fingerprint: str) -> Offer | None:
        pass

    @abstractmethod
    async def get_unseen_for_session(self, session_id: int) -> list[Offer]:
        pass

    @abstractmethod
    async def update_status(self, offer_id: int, status: str) -> None:
        pass

    @abstractmethod
    async def count_for_session(self, session_id: int) -> int:
        pass


class SearchSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: SearchSession) -> None:
        pass

    @abstractmethod
    async def get_by_url(self, url: str) -> SearchSession | None:
        pass

    @abstractmethod
    async def get_by_query(self, query: str) -> SearchSession | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[SearchSession]:
        pass

    @abstractmethod
    async def delete(self, session_id: int) -> None:
        pass


class ScraperPort(ABC):
    """Strategy interface for fetching offers from a web portal.

    Implement this ABC to add a new scraper adapter. Register it in
    ScraperFactory so the factory can auto-detect it from a URL.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier of the classified portal (e.g. 'olx', 'otodom')."""

    @abstractmethod
    async def fetch_offers(
        self, url: str
    ) -> AsyncGenerator[tuple[SyncProgress, list[Offer]]]:
        """Fetch and parse offers from the given search URL.

        Yields (SyncProgress, List[Offer]) tuples per page. On partial failure,
        yields whatever was successfully scraped (D-01/D-05).
        """

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL.

        Used by ScraperFactory to route URLs to the correct adapter (D-06).
        """

    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """Build a portal search URL from a raw query term."""


class SettingsRepository(ABC):
    @abstractmethod
    def get_settings(self) -> Settings:
        pass

    @abstractmethod
    def save_settings(self, settings: Settings) -> None:
        pass
