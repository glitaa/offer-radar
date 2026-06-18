import logging
import re
import httpx

from src.domain.interfaces import ScraperPort
from src.domain.models import Listing
from src.infrastructure.scrapers.base import (
    DEFAULT_HEADERS, 
    fetch_with_retry, 
    polite_delay,
    ScraperBlockedError
)
from src.infrastructure.scrapers.olx_parser import (
    extract_next_data,
    parse_listings_from_json,
    parse_listings_from_html,
    extract_pagination_info
)

logger = logging.getLogger(__name__)

class OlxScraper(ScraperPort):
    """OLX.pl specific implementation of the ScraperPort strategy."""
    
    OLX_URL_PATTERN = re.compile(r"^https?://(?:www\.)?olx\.pl/")
    
    def can_handle(self, url: str) -> bool:
        """Returns True if the URL belongs to OLX.pl."""
        return bool(self.OLX_URL_PATTERN.match(url))
        
    async def fetch_listings(self, url: str) -> list[Listing]:
        """
        Fetch and parse listings from the OLX URL.
        Handles pagination and implements graceful degradation on blocks.
        """
        all_listings = []
        
        # Max pages to fetch to prevent infinite loops or excessive fetching
        MAX_PAGES_TO_FETCH = 10
        
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=httpx.Timeout(30.0)
        ) as client:
            try:
                # 1. Fetch the first page
                response = await fetch_with_retry(client, url)
                html = response.text
                
                # 2. Parse first page
                next_data = extract_next_data(html)
                if next_data:
                    listings = parse_listings_from_json(next_data)
                else:
                    # Fallback to HTML if JSON isn't available
                    logger.warning(f"__NEXT_DATA__ not found on {url}, falling back to HTML parser")
                    listings = parse_listings_from_html(html)
                    
                all_listings.extend(listings)
                
                # 3. Handle Pagination
                pagination = extract_pagination_info(next_data)
                current_page = pagination.get("current_page", 1)
                total_pages = pagination.get("total_pages", 1)
                
                logger.info(f"Fetched page {current_page}/{total_pages} from {url}. Found {len(listings)} listings.")
                
                # Determine base URL for appending page param
                # Handle existing query params correctly
                separator = "&" if "?" in url else "?"
                
                # Fetch subsequent pages
                pages_fetched = 1
                while current_page < total_pages and pages_fetched < MAX_PAGES_TO_FETCH:
                    current_page += 1
                    pages_fetched += 1
                    
                    next_url = f"{url}{separator}page={current_page}"
                    if "page=" in url:
                        # Replace existing page parameter if it was in the original URL
                        next_url = re.sub(r"([?&]page=)\d+", f"\\g<1>{current_page}", url)
                    
                    await polite_delay()
                    
                    try:
                        logger.info(f"Fetching page {current_page}...")
                        page_response = await fetch_with_retry(client, next_url)
                        page_next_data = extract_next_data(page_response.text)
                        
                        if page_next_data:
                            page_listings = parse_listings_from_json(page_next_data)
                        else:
                            page_listings = parse_listings_from_html(page_response.text)
                            
                        all_listings.extend(page_listings)
                        logger.info(f"Found {len(page_listings)} listings on page {current_page}.")
                        
                    except ScraperBlockedError as e:
                        # Graceful degradation (D-01) on subsequent pages
                        logger.warning(f"Scraping blocked during pagination: {e}. Returning {len(all_listings)} listings collected so far.")
                        break
                    except Exception as e:
                        # Log and continue to next page on other errors
                        logger.warning(f"Error processing page {current_page}: {e}")
                        continue
                        
            except ScraperBlockedError as e:
                # Graceful degradation (D-01) on the very first request
                logger.warning(f"Scraping blocked on initial request: {e}. Returning 0 listings.")
                return []
            except Exception as e:
                logger.error(f"Failed to fetch listings from {url}: {e}")
                # We raise here because if the first page completely fails due to network/parsing,
                # the caller needs to know it's a hard failure, not an empty result.
                raise
                
        return all_listings
