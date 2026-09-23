from typing import List, AsyncGenerator, Optional, Union
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
            query = url_or_params.strip()
            # Check by query first
            session = await self._session_repo.get_by_query(query)
            if session:
                return session

            url = self._scraper_factory.build_search_url(query)
            session = await self._session_repo.get_by_url(url)
            if session:
                return session

            session = SearchSession(search_url=url, query=query)
            await self._session_repo.add(session)
            return session
        else:
            url = url_or_params.strip()
            session = await self._session_repo.get_by_url(url)
            if session:
                return session

            session = SearchSession(search_url=url)
            await self._session_repo.add(session)
            return session

    async def sync_offers(
        self,
        session_or_id: Union[SearchSession, int],
        url: Optional[str] = None,
        active_sources: Optional[List[str]] = None,
    ) -> AsyncGenerator[SyncProgress, None]:
        # Handle int ID (backward-compatible signature: sync_offers(session_id, url))
        if isinstance(session_or_id, int):
            session_id = session_or_id
            if url is None:
                raise ValueError("URL must be provided when syncing by session ID")
            scraper = self._scraper_factory.get_scraper(url)
            async for progress, offers in scraper.fetch_offers(url):
                if not offers:
                    yield progress
                    continue

                for offer in offers:
                    offer.session_id = session_id

                await self._offer_repo.add_batch(offers)
                yield progress
            return

        session = session_or_id
        session_id = session.id
        if session_id is None:
            raise ValueError("Session must have an ID to sync offers")

        # If a specific URL was passed or session has no query, sync single URL
        if url is not None or not session.query:
            target_url = url or session.search_url
            scraper = self._scraper_factory.get_scraper(target_url)
            source_name = getattr(scraper, "source_name", "olx")
            async for progress, offers in scraper.fetch_offers(target_url):
                if not offers:
                    yield progress
                    continue

                for offer in offers:
                    offer.session_id = session_id
                    offer.source = source_name

                await self._offer_repo.add_batch(offers)
                yield progress
            return

        # Query session: iterate across all active scrapers
        source_urls = self._scraper_factory.build_search_urls(
            session.query, active_sources=active_sources
        )
        total_found = 0
        for source_name, target_url in source_urls:
            scraper = self._scraper_factory.get_scraper(target_url)
            async for progress, offers in scraper.fetch_offers(target_url):
                if offers:
                    for offer in offers:
                        offer.session_id = session_id
                        offer.source = source_name
                    await self._offer_repo.add_batch(offers)
                    total_found += len(offers)

                yield SyncProgress(
                    current_page=progress.current_page,
                    total_pages=progress.total_pages,
                    total_offers_found=total_found,
                )

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
