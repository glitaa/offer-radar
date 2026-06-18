from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Listing, SearchSession

class ListingRepository(ABC):
    @abstractmethod
    async def add(self, listing: Listing) -> None:
        pass

    @abstractmethod
    async def add_batch(self, listings: List[Listing]) -> None:
        pass
        
    @abstractmethod
    async def get_by_url(self, url: str) -> Optional[Listing]:
        pass

    @abstractmethod
    async def get_unseen_for_session(self, session_id: int) -> List[Listing]:
        pass
        
    @abstractmethod
    async def update_status(self, listing_id: int, status: str) -> None:
        pass

class SearchSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: SearchSession) -> None:
        pass

    @abstractmethod
    async def get_by_url(self, url: str) -> Optional[SearchSession]:
        pass


class ScraperPort(ABC):
    """Strategy interface for fetching listings from a web portal.

    Implement this ABC to add a new scraper adapter. Register it in
    ScraperFactory so the factory can auto-detect it from a URL.
    """

    @abstractmethod
    async def fetch_listings(self, url: str) -> List[Listing]:
        """Fetch and parse listings from the given search URL.

        Returns a list of Listing domain entities. On partial failure,
        returns whatever was successfully scraped (D-01/D-05).
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL.

        Used by ScraperFactory to route URLs to the correct adapter (D-06).
        """
        pass
