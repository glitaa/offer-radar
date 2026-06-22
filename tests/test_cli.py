import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.cli.main import run_loop
from src.domain.models import SearchSession, Offer, OfferStatus, OfferPrice, OfferCategory

@pytest.mark.asyncio
async def test_cli_loop_actions():
    session_manager = AsyncMock()
    session = SearchSession(search_url="https://test.com", id=1)
    
    offer1 = Offer(title="title1", id=10, description="desc1", price=OfferPrice(price_min=100), location="loc1", fingerprint="fp1", urls=[], category=OfferCategory.JOB)
    offer2 = Offer(title="title2", id=20, description="desc2", price=OfferPrice(price_min=200), location="loc2", fingerprint="fp2", urls=[], category=OfferCategory.REAL_ESTATE)
    offer3 = Offer(title="title3", id=30, description="desc3", price=OfferPrice(price_min=300), location="loc3", fingerprint="fp3", urls=[], category=OfferCategory.JOB)
    offer4 = Offer(title="title4", id=40, description="desc4", price=OfferPrice(price_min=400), location="loc4", fingerprint="fp4", urls=[], category=OfferCategory.REAL_ESTATE)
    
    session_manager.get_unseen_offers.return_value = [offer1, offer2, offer3, offer4]
    
    with patch('src.cli.main.msvcrt.getch') as mock_getch:
        # User presses 's' for offer1, 'r' for offer2, 'k' for offer3, 'q' for offer4
        mock_getch.side_effect = [b's', b'r', b'k', b'q']
        
        with patch('src.cli.main.console.print') as mock_print:
            await run_loop(session_manager, session)
            
            # Assert interactions
            session_manager.mark_offer.assert_any_call(10, OfferStatus.SAVED)
            session_manager.mark_offer.assert_any_call(20, OfferStatus.REJECTED)
            # Skip should not change status to something else (stays NEW)
            
            # Check summary text using the mock
            calls = mock_print.call_args_list
            summary_call = next((c for c in calls if "Session Summary - Saved: 1, Rejected: 1, Skipped: 1" in str(c)), None)
            assert summary_call is not None
