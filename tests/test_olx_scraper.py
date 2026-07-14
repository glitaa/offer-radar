import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from src.infrastructure.scrapers.olx_scraper import OlxScraper


@pytest.fixture
def scraper():
    return OlxScraper()


def test_olx_scraper_can_handle(scraper):
    assert scraper.can_handle("https://www.olx.pl/praca/") is True
    assert scraper.can_handle("https://olx.pl/nieruchomosci/") is True
    assert scraper.can_handle("http://olx.pl/d/oferta/123.html") is True

    assert scraper.can_handle("https://otodom.pl/") is False
    assert scraper.can_handle("https://google.com/") is False


@pytest.mark.asyncio
@patch("src.infrastructure.scrapers.base.polite_delay", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_offers_success(mock_get, mock_delay, scraper):
    # Mock first page
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    import json

    state_dict = {
        "listing": {
            "listing": {
                "ads": [{"url": "http://olx.pl/1", "title": "Test"}],
                "pagination": {"currentPage": 1, "totalPages": 1},
            }
        }
    }
    escaped_str = json.dumps(state_dict).replace("/", "\\/").replace('"', '\\"')
    mock_response.text = f'''
    <html><body><script>window.__PRERENDERED_STATE__="{escaped_str}";</script></body></html>
    '''
    mock_get.return_value = mock_response

    offers = []
    async for prog, page_offers in scraper.fetch_offers("https://www.olx.pl/praca/"):
        offers.extend(page_offers)

    assert len(offers) == 1
    assert offers[0].urls[0].url == "http://olx.pl/1"
    assert offers[0].title == "Test"
    assert mock_get.call_count == 1


@pytest.mark.asyncio
@patch("src.infrastructure.scrapers.base.polite_delay", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_offers_graceful_degradation_initial(mock_get, mock_delay, scraper):
    # Mock initial 403
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_get.return_value = mock_response

    # Should return empty list, not raise
    offers = []
    async for prog, page_offers in scraper.fetch_offers("https://www.olx.pl/praca/"):
        offers.extend(page_offers)

    assert len(offers) == 0
    assert mock_get.call_count == 1


@pytest.mark.asyncio
@patch("src.infrastructure.scrapers.base.polite_delay", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_offers_graceful_degradation_pagination(
    mock_get, mock_delay, scraper
):
    # Mock page 1 success, page 2 429 Blocked
    mock_response_p1 = MagicMock(spec=httpx.Response)
    mock_response_p1.status_code = 200
    import json

    state_dict = {
        "listing": {
            "listing": {
                "ads": [{"url": "http://olx.pl/1", "title": "Test1"}],
                "totalPages": 2,
                "currentPage": 1,
            }
        }
    }
    escaped_str = json.dumps(state_dict).replace("/", "\\/").replace('"', '\\"')
    mock_response_p1.text = f'''
    <html><body><script>window.__PRERENDERED_STATE__="{escaped_str}";</script></body></html>
    '''

    mock_response_p2 = MagicMock(spec=httpx.Response)
    mock_response_p2.status_code = 429

    mock_get.side_effect = [mock_response_p1, mock_response_p2]

    offers = []
    async for prog, page_offers in scraper.fetch_offers("https://www.olx.pl/praca/"):
        offers.extend(page_offers)

    # Should return offers from page 1, stop at page 2, not raise
    assert len(offers) == 1
    assert offers[0].urls[0].url == "http://olx.pl/1"
    assert mock_get.call_count == 2


@pytest.mark.asyncio
@patch("src.infrastructure.scrapers.base.asyncio.sleep", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_with_retry_network_error(mock_get, mock_sleep, scraper):
    # Mock httpx.ConnectError twice, then success
    mock_get.side_effect = [
        httpx.ConnectError("Connection failed"),
        httpx.ConnectError("Connection failed"),
        MagicMock(
            status_code=200,
            text='{"props": {"pageProps": {"data": {"ads": [], "pagination": {"totalPages": 1}}}}}',
        ),
    ]

    offers = []
    async for prog, page_offers in scraper.fetch_offers("https://www.olx.pl/praca/"):
        offers.extend(page_offers)
    assert len(offers) == 0
    assert mock_get.call_count == 3
