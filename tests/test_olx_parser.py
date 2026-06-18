import pytest
from src.domain.models import Listing, ListingStatus
from src.infrastructure.scrapers.olx_parser import (
    extract_next_data,
    parse_listings_from_json,
    parse_listings_from_html,
    extract_pagination_info
)

@pytest.fixture
def sample_next_data():
    return {
        "props": {
            "pageProps": {
                "data": {
                    "ads": [
                        {
                            "url": "https://olx.pl/offer/1",
                            "title": "Full Listing",
                            "price": {"value": "1000", "currency": "PLN"},
                            "location": {"city": {"name": "Warszawa"}},
                            "description": "A full description",
                            "extra": "some extra data"
                        },
                        {
                            "url": "https://olx.pl/offer/2",
                            "title": "Partial Listing",
                            "price": None,
                            "location": None
                        },
                        {
                            "title": "Missing URL"
                        }
                    ],
                    "pagination": {
                        "currentPage": 1,
                        "totalPages": 3
                    }
                }
            }
        }
    }

@pytest.fixture
def sample_html():
    return """
    <html>
        <body>
            <script id="__NEXT_DATA__" type="application/json">
                {"props": {"pageProps": {"data": {"ads": []}}}}
            </script>
        </body>
    </html>
    """

def test_extract_next_data(sample_html):
    data = extract_next_data(sample_html)
    assert data == {"props": {"pageProps": {"data": {"ads": []}}}}

def test_extract_next_data_no_script():
    data = extract_next_data("<html><body></body></html>")
    assert data == {}

def test_parse_listings_from_json(sample_next_data):
    listings = parse_listings_from_json(sample_next_data)
    
    assert len(listings) == 2  # The one missing URL is skipped
    
    full = listings[0]
    assert full.url == "https://olx.pl/offer/1"
    assert full.title == "Full Listing"
    assert full.price == "1000 PLN"
    assert full.location == "Warszawa"
    assert full.description == "A full description"
    assert full.extra_data["extra"] == "some extra data"
    assert full.status == ListingStatus.NEW
    
    partial = listings[1]
    assert partial.url == "https://olx.pl/offer/2"
    assert partial.title == "Partial Listing"
    assert partial.price is None
    assert partial.location is None

def test_extract_pagination_info(sample_next_data):
    info = extract_pagination_info(sample_next_data)
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
    <div data-cy="l-card">
        <a href="https://olx.pl/offer/test">
            <h6>Test Listing</h6>
        </a>
    </div>
    '''
    listings = parse_listings_from_html(html)
    assert len(listings) == 1
    assert listings[0].url == "https://olx.pl/offer/test"
    assert listings[0].title == "Test Listing"
