import pytest
import json
from src.domain.models import OfferStatus, OfferCategory
from src.infrastructure.scrapers.olx_parser import (
    extract_prerendered_state,
    parse_offers_from_json,
    parse_offers_from_html,
    extract_pagination_info,
)


@pytest.fixture
def sample_state():
    return {
        "listing": {
            "listing": {
                "ads": [
                    {
                        "urlPath": "/oferta/1",
                        "title": "Full Listing Jobs",
                        "salary": {
                            "from": 5000,
                            "to": 6000,
                            "currencyCode": "PLN",
                            "period": "monthly",
                        },
                        "location": {"pathName": "Warszawa, Mazowieckie"},
                        "description": "A full description",
                        "extra": "some extra data",
                    },
                    {
                        "url": "https://olx.pl/offer/2",
                        "title": "Full Listing RE",
                        "price": {"displayValue": "1000 PLN"},
                        "location": {"cityName": "Kraków"},
                        "description": "A RE description",
                    },
                    {
                        "urlPath": "/oferta/3",
                        "title": "Partial Listing",
                        "salary": None,
                        "price": None,
                        "location": None,
                    },
                    {"title": "Missing URL"},
                ],
                "currentPage": 1,
                "totalPages": 3,
            }
        }
    }


@pytest.fixture
def sample_html():
    state_str = json.dumps({"listing": {"listing": {"ads": []}}})
    # simulate unicode escapes
    escaped_str = state_str.replace("/", "\\/").replace('"', '\\"')
    return f"""
    <html>
        <body>
            <script>window.__PRERENDERED_STATE__="{escaped_str}";</script>
        </body>
    </html>
    """


def test_extract_prerendered_state(sample_html):
    data = extract_prerendered_state(sample_html)
    assert data == {"listing": {"listing": {"ads": []}}}


def test_extract_prerendered_state_no_script():
    data = extract_prerendered_state("<html><body></body></html>")
    assert data == {}


def test_parse_offers_from_json(sample_state):
    offers = parse_offers_from_json(sample_state)

    assert len(offers) == 3  # The one missing URL is skipped

    job = offers[0]
    assert job.urls[0].url == "https://www.olx.pl/oferta/1"
    assert job.title == "Full Listing Jobs"
    assert job.category == OfferCategory.JOB
    assert job.price is not None
    assert job.price.price_min == 5000
    assert job.price.price_max == 6000
    assert job.price.currency == "PLN"
    assert job.price.period == "monthly"
    assert job.location == "Warszawa, Mazowieckie"
    assert job.description == "A full description"
    assert job.extra_data["extra"] == "some extra data"
    assert job.status == OfferStatus.NEW

    re_listing = offers[1]
    assert re_listing.urls[0].url == "https://olx.pl/offer/2"
    assert re_listing.title == "Full Listing RE"
    assert re_listing.category == OfferCategory.REAL_ESTATE
    assert re_listing.price is not None
    assert re_listing.price.price_min == 1000
    assert re_listing.location == "Kraków"

    partial = offers[2]
    assert partial.urls[0].url == "https://www.olx.pl/oferta/3"
    assert partial.title == "Partial Listing"
    assert partial.category is None
    assert partial.price is None
    assert partial.location is None


def test_extract_pagination_info(sample_state):
    info = extract_pagination_info(sample_state)
    assert info["current_page"] == 1
    assert info["total_pages"] == 3
    assert info["has_next"] is True


def test_extract_pagination_info_default():
    info = extract_pagination_info({})
    assert info["current_page"] == 1
    assert info["total_pages"] == 1
    assert info["has_next"] is False


def test_parse_offers_from_html():
    html = """
    <div class="jobs-ad-card">
        <a href="/oferta/test">
            <h6>Test Listing</h6>
        </a>
    </div>
    """
    offers = parse_offers_from_html(html)
    assert len(offers) == 1
    assert offers[0].urls[0].url == "https://www.olx.pl/oferta/test"
    assert offers[0].title == "Test Listing"
