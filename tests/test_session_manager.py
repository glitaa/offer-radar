import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from src.application.session_manager import SessionManager
from src.domain.models import SearchSession, Listing, ListingStatus
from src.application.scraper_factory import ScraperFactory
from src.domain.interfaces import ScraperPort

@pytest.mark.asyncio
async def test_session_manager_start_session():
    session_repo = AsyncMock()
    listing_repo = AsyncMock()
    scraper_factory = MagicMock(spec=ScraperFactory)
    
    manager = SessionManager(session_repo, listing_repo, scraper_factory)
    
    # test query params mapping
    session_repo.get_by_url.return_value = None
    session_repo.add.return_value = None
    
    session = await manager.start_session("laptop")
    assert session.search_url == "https://www.olx.pl/oferty/q-laptop/"
    session_repo.get_by_url.assert_called_with("https://www.olx.pl/oferty/q-laptop/")
    session_repo.add.assert_called_once()
    
    # test retrieval
    existing_session = SearchSession(search_url="https://www.olx.pl/oferty/q-laptop/", id=1)
    session_repo.get_by_url.return_value = existing_session
    session_repo.add.reset_mock()
    
    session = await manager.start_session("laptop")
    assert session.id == 1
    session_repo.add.assert_not_called()

@pytest.mark.asyncio
async def test_session_manager_sync_listings():
    session_repo = AsyncMock()
    listing_repo = AsyncMock()
    scraper_factory = MagicMock(spec=ScraperFactory)
    
    scraper = AsyncMock(spec=ScraperPort)
    scraper_factory.get_scraper.return_value = scraper
    
    mock_listings = [
        Listing(url="test1", title="title1"),
        Listing(url="test2", title="title2"),
    ]
    scraper.fetch_listings.return_value = mock_listings
    
    manager = SessionManager(session_repo, listing_repo, scraper_factory)
    
    await manager.sync_listings(1, "https://test.com")
    
    scraper_factory.get_scraper.assert_called_with("https://test.com")
    scraper.fetch_listings.assert_called_with("https://test.com")
    
    for l in mock_listings:
        assert l.session_id == 1
        
    listing_repo.add_batch.assert_called_once_with(mock_listings)
