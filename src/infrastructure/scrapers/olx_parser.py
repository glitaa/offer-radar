import json
import logging
import re
from bs4 import BeautifulSoup
from src.domain.models import Offer, OfferStatus, OfferUrl

logger = logging.getLogger(__name__)

def extract_prerendered_state(html: str) -> dict:
    """Extracts the window.__PRERENDERED_STATE__ JSON payload from the HTML."""
    try:
        # Match the entire string literal including the quotes
        match = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*(\".*?\");', html)
        if match:
            # First parse the JS string literal into a python string
            # This safely unescapes \u002F and \" without string end issues
            state_str = json.loads(match.group(1))
            # Then parse the JSON string into a dict
            return json.loads(state_str)
    except json.JSONDecodeError:
        logger.warning("Failed to decode JSON from __PRERENDERED_STATE__")
    except Exception as e:
        logger.warning(f"Error extracting __PRERENDERED_STATE__: {e}")
    return {}

def parse_offers_from_json(state: dict) -> list[Offer]:
    """Parses offers from the decoded __PRERENDERED_STATE__ dictionary."""
    offers = []
    try:
        ads = state.get("listing", {}).get("listing", {}).get("ads", [])
        
        for ad in ads:
            try:
                url = ad.get("urlPath") or ad.get("url")
                title = ad.get("title")
                
                if not url or not title:
                    continue # Minimum required fields
                    
                # Handle price (Real Estate) or salary (Jobs)
                price = None
                salary = ad.get("salary")
                if isinstance(salary, dict):
                    sal_from = salary.get("from", "")
                    sal_to = salary.get("to", "")
                    curr = salary.get("currencyCode", "PLN")
                    period = salary.get("period", "")
                    if sal_from and sal_to:
                        price = f"{sal_from} - {sal_to} {curr} / {period}".strip()
                    elif sal_from:
                        price = f"{sal_from} {curr} / {period}".strip()
                else:
                    price_obj = ad.get("price", {})
                    if isinstance(price_obj, dict):
                        price = price_obj.get("displayValue") or price_obj.get("value")
                    elif isinstance(price_obj, str):
                        price = price_obj

                # Handle location
                location_obj = ad.get("location")
                location = None
                if isinstance(location_obj, dict):
                    location = location_obj.get("pathName") or location_obj.get("cityName")
                
                description = ad.get("description")
                
                # Use entire ad object as extra data minus standard fields
                extra_data = {k: v for k, v in ad.items() if k not in ("url", "urlPath", "title", "price", "salary", "location", "description")}
                
                offer = Offer(
                    title=title,
                    fingerprint=url,
                    status=OfferStatus.NEW,
                    price=str(price) if price else None,
                    location=location,
                    description=description,
                    extra_data=extra_data,
                    urls=[OfferUrl(url=url, source="olx")]
                )
                offers.append(offer)
            except Exception as e:
                logger.warning(f"Error parsing individual offer from JSON: {e}")
                
    except Exception as e:
        logger.warning(f"Error parsing offers from JSON: {e}")
        
    return offers

def parse_offers_from_html(html: str) -> list[Offer]:
    """Fallback method to parse offers directly from HTML."""
    offers = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Try both the generic job cards and the old fallback selectors just in case
        cards = soup.select('div.jobs-ad-card') or soup.select('div[data-cy="l-card"]')
        
        for card in cards:
            try:
                a_tag = card.find('a', href=lambda x: x and '/oferta/' in x)
                if not a_tag:
                    # Fallback for old structure
                    a_tag = card.find('a')
                
                if not a_tag or not a_tag.get('href'):
                    continue
                    
                url = str(a_tag['href'])
                
                title_elem = card.find('h6')
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                
                offer = Offer(
                    title=title,
                    fingerprint=url,
                    status=OfferStatus.NEW,
                    urls=[OfferUrl(url=url, source="olx")]
                )
                offers.append(offer)
            except Exception as e:
                logger.warning(f"Error parsing individual offer from HTML: {e}")
    except Exception as e:
        logger.warning(f"Error parsing offers from HTML: {e}")
        
    return offers

def extract_pagination_info(state: dict) -> dict:
    """Extracts pagination info from __PRERENDERED_STATE__."""
    default_info = {"current_page": 1, "total_pages": 1, "has_next": False}
    try:
        listing_meta = state.get("listing", {}).get("listing", {})
        if listing_meta:
            total_pages = listing_meta.get("totalPages", 1)
            current_page = listing_meta.get("currentPage", 1)
            return {
                "current_page": current_page,
                "total_pages": total_pages,
                "has_next": current_page < total_pages
            }
    except Exception as e:
        logger.warning(f"Error extracting pagination info: {e}")
    
    return default_info
