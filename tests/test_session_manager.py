import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.session_manager import SessionManager
from src.domain.models import SearchSession, Offer, OfferUrl
from src.application.scraper_factory import ScraperFactory
from src.domain.interfaces import ScraperPort


@pytest.mark.asyncio
async def test_session_manager_start_session():
    session_repo = AsyncMock()
    offer_repo = AsyncMock()
    scraper_factory = MagicMock(spec=ScraperFactory)
    scraper_factory.build_search_url.return_value = (
        "https://www.olx.pl/oferty/q-laptop/"
    )

    manager = SessionManager(session_repo, offer_repo, scraper_factory)

    # test query params mapping (delegates to scraper_factory.build_search_url)
    session_repo.get_by_url.return_value = None
    session_repo.add.return_value = None

    session = await manager.start_session("laptop")
    assert session.search_url == "https://www.olx.pl/oferty/q-laptop/"
    scraper_factory.build_search_url.assert_called_once_with("laptop")
    session_repo.get_by_url.assert_called_with("https://www.olx.pl/oferty/q-laptop/")
    session_repo.add.assert_called_once()

    # test direct HTTP url (bypasses build_search_url)
    scraper_factory.build_search_url.reset_mock()
    session_repo.get_by_url.return_value = None
    session_repo.add.reset_mock()

    direct_url = "https://www.olx.pl/d/oferty/q-direct/"
    session_direct = await manager.start_session(direct_url)
    assert session_direct.search_url == direct_url
    scraper_factory.build_search_url.assert_not_called()
    session_repo.get_by_url.assert_called_with(direct_url)
    session_repo.add.assert_called_once()

    # test retrieval of existing session
    existing_session = SearchSession(
        search_url="https://www.olx.pl/oferty/q-laptop/", id=1
    )
    session_repo.get_by_url.return_value = existing_session
    session_repo.add.reset_mock()

    session = await manager.start_session("laptop")
    assert session.id == 1
    session_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_session_manager_sync_offers():
    session_repo = AsyncMock()
    offer_repo = AsyncMock()
    scraper_factory = MagicMock(spec=ScraperFactory)

    scraper = AsyncMock(spec=ScraperPort)
    scraper_factory.get_scraper.return_value = scraper

    mock_offers = [
        Offer(fingerprint="test1", urls=[OfferUrl(url="test1")], title="title1"),
        Offer(fingerprint="test2", urls=[OfferUrl(url="test2")], title="title2"),
    ]

    # Mock the async generator
    from src.domain.models import SyncProgress

    async def mock_fetch_offers(url):
        yield SyncProgress(1, 1, 2), mock_offers

    scraper.fetch_offers = mock_fetch_offers

    manager = SessionManager(session_repo, offer_repo, scraper_factory)

    # consume the generator
    async for progress in manager.sync_offers(1, "https://test.com"):
        pass

    scraper_factory.get_scraper.assert_called_with("https://test.com")

    for offer in mock_offers:
        assert offer.session_id == 1

    offer_repo.add_batch.assert_called_once_with(mock_offers)
