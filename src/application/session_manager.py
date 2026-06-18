from typing import List
from src.domain.interfaces import ListingRepository, SearchSessionRepository
from src.application.scraper_factory import ScraperFactory
from src.domain.models import Listing, SearchSession, ListingStatus

class SessionManager:
    def __init__(
        self,
        session_repo: SearchSessionRepository,
        listing_repo: ListingRepository,
        scraper_factory: ScraperFactory
    ):
        self._session_repo = session_repo
        self._listing_repo = listing_repo
        self._scraper_factory = scraper_factory

    async def start_session(self, url_or_params: str) -> SearchSession:
        if not url_or_params.startswith("http"):
            url = f"https://www.olx.pl/oferty/q-{url_or_params}/"
        else:
            url = url_or_params

        session = await self._session_repo.get_by_url(url)
        if session:
            return session

        session = SearchSession(search_url=url)
        await self._session_repo.add(session)
        return session

    async def sync_listings(self, session_id: int, url: str) -> None:
        scraper = self._scraper_factory.get_scraper(url)
        listings = await scraper.fetch_listings(url)
        
        for listing in listings:
            listing.session_id = session_id
            
        await self._listing_repo.add_batch(listings)

    async def get_unseen_listings(self, session_id: int) -> List[Listing]:
        return await self._listing_repo.get_unseen_for_session(session_id)

    async def mark_listing(self, listing_id: int, status: ListingStatus) -> None:
        await self._listing_repo.update_status(listing_id, status.value)
