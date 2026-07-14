from typing import List, AsyncGenerator
from src.domain.interfaces import OfferRepository, SearchSessionRepository
from src.application.scraper_factory import ScraperFactory
from src.domain.models import Offer, SearchSession, OfferStatus, SyncProgress


class SessionManager:
    def __init__(
        self,
        session_repo: SearchSessionRepository,
        offer_repo: OfferRepository,
        scraper_factory: ScraperFactory,
    ):
        self._session_repo = session_repo
        self._offer_repo = offer_repo
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

    async def sync_offers(
        self, session_id: int, url: str
    ) -> AsyncGenerator[SyncProgress, None]:
        scraper = self._scraper_factory.get_scraper(url)

        async for progress, offers in scraper.fetch_offers(url):
            if not offers:
                yield progress
                continue

            for offer in offers:
                offer.session_id = session_id

            await self._offer_repo.add_batch(offers)
            yield progress

    async def get_unseen_offers(self, session_id: int) -> List[Offer]:
        return await self._offer_repo.get_unseen_for_session(session_id)

    async def mark_offer(self, offer_id: int, status: OfferStatus) -> None:
        await self._offer_repo.update_status(offer_id, status.value)

    async def get_all_sessions(self) -> List[SearchSession]:
        return await self._session_repo.get_all()

    async def delete_session(self, session_id: int) -> None:
        await self._session_repo.delete(session_id)

    async def count_offers_for_session(self, session_id: int) -> int:
        return await self._offer_repo.count_for_session(session_id)
