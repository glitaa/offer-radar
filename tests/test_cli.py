import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.cli.main import run_loop
from src.domain.models import SearchSession, Listing, ListingStatus

@pytest.mark.asyncio
async def test_cli_loop_actions():
    session_manager = AsyncMock()
    session = SearchSession(search_url="https://test.com", id=1)
    
    listing1 = Listing(url="url1", title="title1", id=10, description="desc1", price="100", location="loc1")
    listing2 = Listing(url="url2", title="title2", id=20, description="desc2", price="200", location="loc2")
    listing3 = Listing(url="url3", title="title3", id=30, description="desc3", price="300", location="loc3")
    listing4 = Listing(url="url4", title="title4", id=40, description="desc4", price="400", location="loc4")
    
    session_manager.get_unseen_listings.return_value = [listing1, listing2, listing3, listing4]
    
    with patch('src.cli.main.msvcrt.getch') as mock_getch:
        # User presses 's' for listing1, 'r' for listing2, 'k' for listing3, 'q' for listing4
        mock_getch.side_effect = [b's', b'r', b'k', b'q']
        
        with patch('src.cli.main.console.print') as mock_print:
            await run_loop(session_manager, session)
            
            # Assert interactions
            session_manager.mark_listing.assert_any_call(10, ListingStatus.SAVED)
            session_manager.mark_listing.assert_any_call(20, ListingStatus.REJECTED)
            # Skip should not change status to something else (stays NEW)
            
            # Check summary text using the mock
            calls = mock_print.call_args_list
            summary_call = next((c for c in calls if "Session Summary - Saved: 1, Rejected: 1, Skipped: 1" in str(c)), None)
            assert summary_call is not None
