from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Offer, SearchSession

class OfferRepository(ABC):
    @abstractmethod
    async def add(self, offer: Offer) -> None:
        pass

    @abstractmethod
    async def add_batch(self, offers: List[Offer]) -> None:
        pass
        
    @abstractmethod
    async def get_by_fingerprint(self, fingerprint: str) -> Optional[Offer]:
        pass

    @abstractmethod
    async def get_unseen_for_session(self, session_id: int) -> List[Offer]:
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
    async def get_by_url(self, url: str) -> Optional[SearchSession]:
        pass

    @abstractmethod
    async def get_all(self) -> List[SearchSession]:
        pass

    @abstractmethod
    async def delete(self, session_id: int) -> None:
        pass


class ScraperPort(ABC):
    """Strategy interface for fetching offers from a web portal.

    Implement this ABC to add a new scraper adapter. Register it in
    ScraperFactory so the factory can auto-detect it from a URL.
    """

    @abstractmethod
    async def fetch_offers(self, url: str) -> List[Offer]:
        """Fetch and parse offers from the given search URL.

        Returns a list of Offer domain entities. On partial failure,
        returns whatever was successfully scraped (D-01/D-05).
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL.

        Used by ScraperFactory to route URLs to the correct adapter (D-06).
        """
        pass
