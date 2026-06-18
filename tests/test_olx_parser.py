import pytest
import json
from src.domain.models import Listing, ListingStatus
from src.infrastructure.scrapers.olx_parser import (
    extract_prerendered_state,
    parse_listings_from_json,
    parse_listings_from_html,
    extract_pagination_info
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
                        "salary": {"from": 5000, "to": 6000, "currencyCode": "PLN", "period": "monthly"},
                        "location": {"pathName": "Warszawa, Mazowieckie"},
                        "description": "A full description",
                        "extra": "some extra data"
                    },
                    {
                        "url": "https://olx.pl/offer/2",
                        "title": "Full Listing RE",
                        "price": {"displayValue": "1000 PLN"},
                        "location": {"cityName": "Kraków"},
                        "description": "A RE description"
                    },
                    {
                        "urlPath": "/oferta/3",
                        "title": "Partial Listing",
                        "salary": None,
                        "price": None,
                        "location": None
                    },
                    {
                        "title": "Missing URL"
                    }
                ],
                "currentPage": 1,
                "totalPages": 3
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

def test_parse_listings_from_json(sample_state):
    listings = parse_listings_from_json(sample_state)
    
    assert len(listings) == 3  # The one missing URL is skipped
    
    job = listings[0]
    assert job.url == "/oferta/1"
    assert job.title == "Full Listing Jobs"
    assert job.price == "5000 - 6000 PLN / monthly"
    assert job.location == "Warszawa, Mazowieckie"
    assert job.description == "A full description"
    assert job.extra_data["extra"] == "some extra data"
    assert job.status == ListingStatus.NEW
    
    re_listing = listings[1]
    assert re_listing.url == "https://olx.pl/offer/2"
    assert re_listing.title == "Full Listing RE"
    assert re_listing.price == "1000 PLN"
    assert re_listing.location == "Kraków"
    
    partial = listings[2]
    assert partial.url == "/oferta/3"
    assert partial.title == "Partial Listing"
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

def test_parse_listings_from_html():
    html = '''
    <div class="jobs-ad-card">
        <a href="/oferta/test">
            <h6>Test Listing</h6>
        </a>
    </div>
    '''
    listings = parse_listings_from_html(html)
    assert len(listings) == 1
    assert listings[0].url == "/oferta/test"
    assert listings[0].title == "Test Listing"

