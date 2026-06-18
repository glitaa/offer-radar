import asyncio
import random
import httpx
from typing import Tuple

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

DEFAULT_DELAY_RANGE = (1.0, 3.0)
MAX_RETRIES = 3

class ScraperBlockedError(Exception):
    """Raised when the scraper encounters a 403 or 429 block (D-01)."""
    pass

class ScraperNetworkError(Exception):
    """Raised when the scraper encounters persistent network failures after retries."""
    pass

async def polite_delay(delay_range: Tuple[float, float] = DEFAULT_DELAY_RANGE) -> None:
    """Sleep for a random duration between delay_range[0] and delay_range[1]."""
    await asyncio.sleep(random.uniform(*delay_range))

async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = MAX_RETRIES
) -> httpx.Response:
    """
    Fetch a URL using httpx with exponential backoff for network errors.
    Immediately raises ScraperBlockedError on 403 or 429 to trigger graceful degradation.
    """
    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            
            # Immediately stop and trigger D-01 graceful degradation on blocks
            if response.status_code in (403, 429):
                raise ScraperBlockedError(f"Access blocked by portal: HTTP {response.status_code}")
                
            # If successful, return the response
            if response.status_code == 200:
                return response
                
            # For other non-200 codes, we might want to retry (e.g. 500, 502, 503, 504)
            response.raise_for_status()
            
        except httpx.RequestError as e:
            # Re-raise network errors on the final attempt
            if attempt == max_retries - 1:
                raise ScraperNetworkError(f"Network error after {max_retries} attempts: {e}") from e
                
        except httpx.HTTPStatusError as e:
            # Re-raise non-block HTTP errors on the final attempt
            if attempt == max_retries - 1:
                raise ScraperNetworkError(f"HTTP error after {max_retries} attempts: {e}") from e

        # Exponential backoff: 1s, 2s, 4s plus a little jitter
        delay = (2 ** attempt) + random.uniform(0, 1)
        await asyncio.sleep(delay)
        
    raise ScraperNetworkError(f"Failed to fetch {url} after {max_retries} attempts")
