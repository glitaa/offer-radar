from typing import List
from src.domain.interfaces import ScraperPort
from src.infrastructure.scrapers.olx_scraper import OlxScraper


class ScraperFactory:
    """Factory that auto-detects the appropriate scraper based on URL (D-06)."""

    def __init__(self, scrapers: List[ScraperPort]):
        self._scrapers = scrapers

    def get_scraper(self, url: str) -> ScraperPort:
        """Return the first scraper that can handle the given URL."""
        for scraper in self._scrapers:
            if scraper.can_handle(url):
                return scraper
        raise ValueError(f"No scraper available for URL: {url}")

    @classmethod
    def create_default(cls) -> "ScraperFactory":
        """Convenience method to create a factory with default scrapers registered."""
        return cls([OlxScraper()])
