from src.application.scraper_factory import ScraperFactory
from src.infrastructure.scrapers.olx_scraper import OlxScraper


def create_default_scraper_factory() -> ScraperFactory:
    """Create a ScraperFactory with all built-in scrapers registered."""
    factory = ScraperFactory()
    factory.register(OlxScraper())
    return factory
