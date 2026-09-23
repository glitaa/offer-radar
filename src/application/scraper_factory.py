from typing import List, Optional
from src.domain.interfaces import ScraperPort


class ScraperFactory:
    """Factory that routes URLs to the appropriate scraper and manages registered scrapers (D-06)."""

    def __init__(self, scrapers: Optional[List[ScraperPort]] = None):
        self._scrapers: List[ScraperPort] = (
            list(scrapers) if scrapers is not None else []
        )

    def register(self, scraper: ScraperPort) -> None:
        """Register a scraper adapter with the factory."""
        self._scrapers.append(scraper)

    def get_scraper(self, url: str) -> ScraperPort:
        """Return the first scraper that can handle the given URL."""
        for scraper in self._scrapers:
            if scraper.can_handle(url):
                return scraper
        raise ValueError(f"No scraper available for URL: {url}")

    def build_search_url(self, query: str) -> str:
        """Build a search URL using the default registered scraper."""
        if not self._scrapers:
            raise ValueError("No scrapers registered")
        return self._scrapers[0].build_search_url(query)
