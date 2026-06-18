import json
import logging
from bs4 import BeautifulSoup
from src.domain.models import Listing, ListingStatus

logger = logging.getLogger(__name__)

def extract_next_data(html: str) -> dict:
    try:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if script and script.string:
            return json.loads(script.string)
    except json.JSONDecodeError:
        pass
    except Exception as e:
        logger.warning(f"Error extracting __NEXT_DATA__: {e}")
    return {}

def parse_listings_from_json(next_data: dict) -> list[Listing]:
    listings = []
    try:
        # Navigate __NEXT_DATA__ structure. This path may change.
        # Fallback empty lists dict.get is used to be safe.
        ads = next_data.get("props", {}).get("pageProps", {}).get("data", {}).get("ads", [])
        
        for ad in ads:
            try:
                url = ad.get("url")
                title = ad.get("title")
                
                if not url or not title:
                    continue # Minimum required fields
                    
                price_obj = ad.get("price", {})
                price = None
                if price_obj and "value" in price_obj:
                    # e.g., "1000 PLN"
                    price = f"{price_obj.get('value')} {price_obj.get('currency', '')}".strip()
                    
                location_obj = ad.get("location", {})
                location = location_obj.get("city", {}).get("name") if location_obj else None
                
                description = ad.get("description")
                
                # Use entire ad object as extra data minus standard fields
                extra_data = {k: v for k, v in ad.items() if k not in ("url", "title", "price", "location", "description")}
                
                listing = Listing(
                    url=url,
                    title=title,
                    status=ListingStatus.NEW,
                    price=price,
                    location=location,
                    description=description,
                    extra_data=extra_data
                )
                listings.append(listing)
            except Exception as e:
                logger.warning(f"Error parsing individual listing from JSON: {e}")
                
    except Exception as e:
        logger.warning(f"Error parsing listings from JSON: {e}")
        
    return listings

def parse_listings_from_html(html: str) -> list[Listing]:
    """Fallback method to parse listings directly from HTML."""
    listings = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Typical listing card selector (this is fragile)
        cards = soup.select('div[data-cy="l-card"]')
        
        for card in cards:
            try:
                a_tag = card.find('a')
                if not a_tag or not a_tag.get('href'):
                    continue
                url = str(a_tag['href'])
                
                title_elem = card.find('h6')
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                
                # Very basic extraction for fallback
                listing = Listing(
                    url=url,
                    title=title,
                    status=ListingStatus.NEW
                )
                listings.append(listing)
            except Exception as e:
                logger.warning(f"Error parsing individual listing from HTML: {e}")
    except Exception as e:
        logger.warning(f"Error parsing listings from HTML: {e}")
        
    return listings

def extract_pagination_info(next_data: dict) -> dict:
    default_info = {"current_page": 1, "total_pages": 1, "has_next": False}
    try:
        pagination = next_data.get("props", {}).get("pageProps", {}).get("data", {}).get("pagination", {})
        if pagination:
            total_pages = pagination.get("totalPages", 1)
            current_page = pagination.get("currentPage", 1)
            return {
                "current_page": current_page,
                "total_pages": total_pages,
                "has_next": current_page < total_pages
            }
    except Exception as e:
        logger.warning(f"Error extracting pagination info: {e}")
    
    return default_info
