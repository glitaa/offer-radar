from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Listing, SearchSession

class ListingRepository(ABC):
    @abstractmethod
    async def add(self, listing: Listing) -> None:
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
