import pytest
from src.application.scraper_factory import ScraperFactory
from src.infrastructure.scrapers.olx_scraper import OlxScraper


def test_scraper_factory_get_scraper():
    factory = ScraperFactory.create_default()

    scraper = factory.get_scraper("https://www.olx.pl/praca/")
    assert isinstance(scraper, OlxScraper)


def test_scraper_factory_unsupported_url():
    factory = ScraperFactory.create_default()

    with pytest.raises(ValueError) as exc:
        factory.get_scraper("https://www.otodom.pl/wynajem")

    assert "No scraper available for URL" in str(exc.value)


def test_scraper_factory_build_search_url():
    factory = ScraperFactory.create_default()
    assert factory.build_search_url("laptop") == "https://www.olx.pl/oferty/q-laptop/"


def test_scraper_factory_build_search_url_no_scrapers():
    factory = ScraperFactory([])
    with pytest.raises(ValueError, match="No scrapers registered"):
        factory.build_search_url("laptop")
