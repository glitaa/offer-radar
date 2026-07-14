import json
import logging
import re
from bs4 import BeautifulSoup
from src.domain.models import Offer, OfferStatus, OfferUrl, OfferPrice, OfferCategory

logger = logging.getLogger(__name__)


def extract_prerendered_state(html: str) -> dict:
    """Extracts the window.__PRERENDERED_STATE__ JSON payload from the HTML."""
    try:
        # Match the entire string literal including the quotes
        match = re.search(r"window\.__PRERENDERED_STATE__\s*=\s*(\".*?\");", html)
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
                    continue  # Minimum required fields

                if url and not url.startswith("http"):
                    if not url.startswith("/"):
                        url = "/" + url
                    url = f"https://www.olx.pl{url}"

                # Handle category (Real Estate or Jobs)
                category = None
                salary = ad.get("salary")
                price_obj = ad.get("price", {})
                is_real_estate = "/nieruchomosci/" in url

                if salary:
                    category = OfferCategory.JOB
                elif is_real_estate or (price_obj and not salary):
                    category = OfferCategory.REAL_ESTATE

                # Handle price flags and numeric values
                price = None
                price_min = None
                price_max = None
                currency = None
                period = None
                is_free = False
                is_negotiable = False

                if isinstance(price_obj, dict):
                    display_value = str(
                        price_obj.get("displayValue") or price_obj.get("value") or ""
                    ).lower()
                    if "za darmo" in display_value:
                        is_free = True
                    if (
                        "do negocjacji" in display_value
                        or price_obj.get("isNegotiable") is True
                    ):
                        is_negotiable = True
                elif isinstance(price_obj, str):
                    display_value = price_obj.lower()
                    if "za darmo" in display_value:
                        is_free = True
                    if "do negocjacji" in display_value:
                        is_negotiable = True

                if category == OfferCategory.JOB and isinstance(salary, dict):
                    sal_from = salary.get("from")
                    sal_to = salary.get("to")
                    currency = salary.get("currencyCode", "PLN")
                    period = salary.get("type") or salary.get("period")

                    try:
                        price_min = float(sal_from) if sal_from is not None else None
                    except ValueError:
                        pass
                    try:
                        price_max = float(sal_to) if sal_to is not None else None
                    except ValueError:
                        pass
                elif category == OfferCategory.REAL_ESTATE:
                    if isinstance(price_obj, dict):
                        reg_price = price_obj.get("regularPrice", {})
                        if isinstance(reg_price, dict):
                            val = reg_price.get("value")
                            currency = reg_price.get("currencyCode", "PLN")
                            if val is not None:
                                try:
                                    price_min = float(val)
                                except ValueError:
                                    pass

                        if (
                            price_min is None
                            and not is_free
                            and price_obj.get("displayValue")
                        ):
                            num_str = re.sub(
                                r"[^\d\.\,]",
                                "",
                                price_obj.get("displayValue").replace(",", "."),
                            )
                            if num_str:
                                try:
                                    price_min = float(num_str)
                                except ValueError:
                                    pass

                if (
                    price_min is not None
                    or price_max is not None
                    or is_free
                    or is_negotiable
                ):
                    price = OfferPrice(
                        price_min=price_min,
                        price_max=price_max,
                        currency=currency,
                        period=period,
                        is_free=is_free,
                        is_negotiable=is_negotiable,
                    )

                # Handle location
                location_obj = ad.get("location")
                location = None
                if isinstance(location_obj, dict):
                    location = location_obj.get("pathName") or location_obj.get(
                        "cityName"
                    )

                description = ad.get("description")

                # Use entire ad object as extra data minus standard fields
                extra_data = {
                    k: v
                    for k, v in ad.items()
                    if k
                    not in (
                        "url",
                        "urlPath",
                        "title",
                        "price",
                        "salary",
                        "location",
                        "description",
                    )
                }

                offer = Offer(
                    title=title,
                    fingerprint=url,
                    status=OfferStatus.NEW,
                    price=price,
                    category=category,
                    location=location,
                    description=description,
                    extra_data=extra_data,
                    urls=[OfferUrl(url=url)],
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
        cards = soup.select("div.jobs-ad-card") or soup.select('div[data-cy="l-card"]')

        for card in cards:
            try:
                a_tag = card.find("a", href=lambda x: x and "/oferta/" in x)
                if not a_tag:
                    # Fallback for old structure
                    a_tag = card.find("a")

                if not a_tag or not a_tag.get("href"):
                    continue

                url = str(a_tag["href"])
                if url and not url.startswith("http"):
                    if not url.startswith("/"):
                        url = "/" + url
                    url = f"https://www.olx.pl{url}"

                title_elem = card.find("h6")
                title = title_elem.text.strip() if title_elem else "Unknown Title"

                offer = Offer(
                    title=title,
                    fingerprint=url,
                    status=OfferStatus.NEW,
                    price=None,
                    category=None,
                    urls=[OfferUrl(url=url)],
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
                "has_next": current_page < total_pages,
            }
    except Exception as e:
        logger.warning(f"Error extracting pagination info: {e}")

    return default_info
