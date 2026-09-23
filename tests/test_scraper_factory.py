from unittest.mock import MagicMock
import pytest

from src.application.scraper_factory import ScraperFactory
from src.domain.interfaces import ScraperPort
from src.infrastructure.scrapers.factory import create_default_scraper_factory
from src.infrastructure.scrapers.olx_scraper import OlxScraper


def test_scraper_factory_register_and_get():
    mock_scraper = MagicMock(spec=ScraperPort)
    mock_scraper.can_handle.side_effect = lambda url: "example.com" in url

    factory = ScraperFactory()
    factory.register(mock_scraper)

    scraper = factory.get_scraper("https://example.com/test")
    assert scraper is mock_scraper
    mock_scraper.can_handle.assert_called_with("https://example.com/test")


def test_scraper_factory_unsupported_url():
    factory = ScraperFactory()

    with pytest.raises(ValueError) as exc:
        factory.get_scraper("https://www.otodom.pl/wynajem")

    assert "No scraper available for URL" in str(exc.value)


def test_scraper_factory_build_search_url():
    mock_scraper = MagicMock(spec=ScraperPort)
    mock_scraper.build_search_url.return_value = "https://example.com/search?q=laptop"

    factory = ScraperFactory([mock_scraper])
    assert factory.build_search_url("laptop") == "https://example.com/search?q=laptop"
    mock_scraper.build_search_url.assert_called_once_with("laptop")


def test_scraper_factory_build_search_url_no_scrapers():
    factory = ScraperFactory([])
    with pytest.raises(ValueError, match="No scrapers registered"):
        factory.build_search_url("laptop")


def test_scraper_factory_multi_source_discovery_and_filtering():
    s1 = MagicMock(spec=ScraperPort)
    s1.source_name = "olx"
    s1.build_search_url.return_value = "https://olx.pl/q-phone"

    s2 = MagicMock(spec=ScraperPort)
    s2.source_name = "otodom"
    s2.build_search_url.return_value = "https://otodom.pl/q-phone"

    factory = ScraperFactory([s1, s2])

    assert factory.get_available_sources() == ["olx", "otodom"]
    assert factory.get_scrapers() == [s1, s2]
    assert factory.get_scrapers(["otodom"]) == [s2]
    assert factory.get_scraper_by_source("olx") is s1
    assert factory.get_scraper_by_source("nonexistent") is None

    urls = factory.build_search_urls("phone", active_sources=["olx", "otodom"])
    assert urls == [
        ("olx", "https://olx.pl/q-phone"),
        ("otodom", "https://otodom.pl/q-phone"),
    ]

    urls_single = factory.build_search_urls("phone", active_sources=["olx"])
    assert urls_single == [("olx", "https://olx.pl/q-phone")]


def test_create_default_scraper_factory():
    factory = create_default_scraper_factory()
    scraper = factory.get_scraper("https://www.olx.pl/praca/")
    assert isinstance(scraper, OlxScraper)
    assert factory.build_search_url("laptop") == "https://www.olx.pl/oferty/q-laptop/"
