from typing import List, Optional, Tuple
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

    def get_available_sources(self) -> List[str]:
        """Return a list of source identifiers from all registered scrapers."""
        return [s.source_name for s in self._scrapers]

    def get_scrapers(
        self, active_sources: Optional[List[str]] = None
    ) -> List[ScraperPort]:
        """Return scrapers filtered by active source names, or all registered scrapers if active_sources is None."""
        if active_sources is None:
            return list(self._scrapers)
        sources_set = set(active_sources)
        return [s for s in self._scrapers if s.source_name in sources_set]

    def get_scraper_by_source(self, source_name: str) -> Optional[ScraperPort]:
        """Return the scraper corresponding to the given source identifier."""
        for scraper in self._scrapers:
            if scraper.source_name == source_name:
                return scraper
        return None

    def build_search_urls(
        self, query: str, active_sources: Optional[List[str]] = None
    ) -> List[Tuple[str, str]]:
        """Build search URLs for all active scrapers.

        Returns a list of (source_name, search_url) tuples.
        """
        scrapers = self.get_scrapers(active_sources)
        return [(s.source_name, s.build_search_url(query)) for s in scrapers]

    def build_search_url(
        self, query: str, active_sources: Optional[List[str]] = None
    ) -> str:
        """Build a search URL using the first active registered scraper."""
        scrapers = self.get_scrapers(active_sources)
        if not scrapers:
            raise ValueError("No scrapers registered")
        return scrapers[0].build_search_url(query)
