import logging
import re
import httpx

from typing import AsyncGenerator, Tuple
from src.domain.interfaces import ScraperPort
from src.domain.models import Offer, SyncProgress
from src.infrastructure.scrapers.base import (
    DEFAULT_HEADERS,
    fetch_with_retry,
    polite_delay,
    ScraperBlockedError,
)
from src.infrastructure.scrapers.olx_parser import (
    extract_prerendered_state,
    parse_offers_from_json,
    parse_offers_from_html,
    extract_pagination_info,
)

logger = logging.getLogger(__name__)


class OlxScraper(ScraperPort):
    """OLX.pl specific implementation of the ScraperPort strategy."""

    OLX_URL_PATTERN = re.compile(r"^https?://(?:www\.)?olx\.pl/")

    def can_handle(self, url: str) -> bool:
        """Returns True if the URL belongs to OLX.pl."""
        return bool(self.OLX_URL_PATTERN.match(url))

    async def fetch_offers(
        self, url: str
    ) -> AsyncGenerator[Tuple[SyncProgress, list[Offer]], None]:
        """
        Fetch and parse offers from the OLX URL iteratively.
        Handles pagination and implements graceful degradation on blocks.
        """
        total_offers_found = 0

        # Max pages to fetch to prevent infinite loops or excessive fetching
        MAX_PAGES_TO_FETCH = 10

        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS, follow_redirects=True, timeout=httpx.Timeout(30.0)
        ) as client:
            try:
                # 1. Fetch the first page
                response = await fetch_with_retry(client, url)
                html = response.text

                # 2. Parse first page
                state = extract_prerendered_state(html)
                if state:
                    offers = parse_offers_from_json(state)
                else:
                    # Fallback to HTML if JSON isn't available
                    logger.warning(
                        f"__PRERENDERED_STATE__ not found on {url}, falling back to HTML parser"
                    )
                    offers = parse_offers_from_html(html)

                total_offers_found += len(offers)

                # 3. Handle Pagination
                pagination = extract_pagination_info(state)
                current_page = pagination.get("current_page", 1)
                total_pages = min(pagination.get("total_pages", 1), MAX_PAGES_TO_FETCH)

                logger.info(
                    f"Fetched page {current_page}/{total_pages} from {url}. Found {len(offers)} offers."
                )

                yield (
                    SyncProgress(current_page, total_pages, total_offers_found),
                    offers,
                )

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
                        next_url = re.sub(
                            r"([?&]page=)\d+", f"\\g<1>{current_page}", url
                        )

                    await polite_delay()

                    try:
                        logger.info(f"Fetching page {current_page}...")
                        page_response = await fetch_with_retry(client, next_url)
                        page_state = extract_prerendered_state(page_response.text)

                        if page_state:
                            page_offers = parse_offers_from_json(page_state)
                        else:
                            page_offers = parse_offers_from_html(page_response.text)

                        total_offers_found += len(page_offers)
                        logger.info(
                            f"Found {len(page_offers)} offers on page {current_page}."
                        )

                        yield (
                            SyncProgress(current_page, total_pages, total_offers_found),
                            page_offers,
                        )

                    except ScraperBlockedError as e:
                        # Graceful degradation (D-01) on subsequent pages
                        logger.warning(
                            f"Scraping blocked during pagination: {e}. Stopping iteration."
                        )
                        break
                    except Exception as e:
                        # Log and continue to next page on other errors
                        logger.warning(f"Error processing page {current_page}: {e}")
                        continue

            except ScraperBlockedError as e:
                # Graceful degradation (D-01) on the very first request
                logger.warning(
                    f"Scraping blocked on initial request: {e}. Returning 0 offers."
                )
                return
            except Exception as e:
                logger.error(f"Failed to fetch offers from {url}: {e}")
                # We raise here because if the first page completely fails due to network/parsing,
                # the caller needs to know it's a hard failure, not an empty result.
                raise
