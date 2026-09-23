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
    session_repo.get_by_query.return_value = None
    session_repo.get_by_url.return_value = None
    session_repo.add.return_value = None

    session = await manager.start_session("laptop")
    assert session.search_url == "https://www.olx.pl/oferty/q-laptop/"
    assert session.query == "laptop"
    scraper_factory.build_search_url.assert_called_once_with("laptop")
    session_repo.get_by_query.assert_called_with("laptop")
    session_repo.add.assert_called_once()

    # test direct HTTP url (bypasses build_search_url)
    scraper_factory.build_search_url.reset_mock()
    session_repo.get_by_url.return_value = None
    session_repo.add.reset_mock()

    direct_url = "https://www.olx.pl/d/oferty/q-direct/"
    session_direct = await manager.start_session(direct_url)
    assert session_direct.search_url == direct_url
    assert session_direct.query is None
    scraper_factory.build_search_url.assert_not_called()
    session_repo.get_by_url.assert_called_with(direct_url)
    session_repo.add.assert_called_once()

    # test retrieval of existing session by query
    existing_session = SearchSession(
        search_url="https://www.olx.pl/oferty/q-laptop/", query="laptop", id=1
    )
    session_repo.get_by_query.return_value = existing_session
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

    # consume the generator with int session_id
    async for progress in manager.sync_offers(1, "https://test.com"):
        pass

    scraper_factory.get_scraper.assert_called_with("https://test.com")

    for offer in mock_offers:
        assert offer.session_id == 1

    offer_repo.add_batch.assert_called_once_with(mock_offers)


@pytest.mark.asyncio
async def test_session_manager_multi_source_sync_offers():
    session_repo = AsyncMock()
    offer_repo = AsyncMock()
    scraper_factory = MagicMock(spec=ScraperFactory)

    session = SearchSession(
        id=42,
        query="python",
        search_url="https://olx.pl/q-python",
    )

    scraper_factory.build_search_urls.return_value = [
        ("olx", "https://olx.pl/q-python"),
        ("otodom", "https://otodom.pl/q-python"),
    ]

    scraper_olx = AsyncMock(spec=ScraperPort)
    scraper_otodom = AsyncMock(spec=ScraperPort)

    def get_scraper_mock(url):
        if "olx.pl" in url:
            return scraper_olx
        return scraper_otodom

    scraper_factory.get_scraper.side_effect = get_scraper_mock

    offer_olx = Offer(title="olx offer", urls=[OfferUrl("http://olx.pl/1")])
    offer_otodom = Offer(title="otodom offer", urls=[OfferUrl("http://otodom.pl/2")])

    from src.domain.models import SyncProgress

    async def mock_fetch_olx(url):
        yield SyncProgress(1, 1, 1), [offer_olx]

    async def mock_fetch_otodom(url):
        yield SyncProgress(1, 1, 1), [offer_otodom]

    scraper_olx.fetch_offers = mock_fetch_olx
    scraper_otodom.fetch_offers = mock_fetch_otodom

    manager = SessionManager(session_repo, offer_repo, scraper_factory)

    progresses = []
    async for prog in manager.sync_offers(session, active_sources=["olx", "otodom"]):
        progresses.append(prog)

    scraper_factory.build_search_urls.assert_called_once_with(
        "python", active_sources=["olx", "otodom"]
    )
    assert offer_olx.session_id == 42
    assert offer_olx.source == "olx"
    assert offer_otodom.session_id == 42
    assert offer_otodom.source == "otodom"
    assert offer_repo.add_batch.call_count == 2
    assert progresses[-1].total_offers_found == 2
