import hashlib
import re
from typing import Optional

def generate_offer_fingerprint(title: str, description: Optional[str], price: Optional[str] = None) -> str:
    """
    Generates a unique fingerprint for an offer to deduplicate cross-postings and re-uploads.
    Includes title, first part of description, and price.
    """
    def normalize(text: Optional[str]) -> str:
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove punctuation and non-alphanumeric chars
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace (just completely strip it for robustness)
        text = re.sub(r'\s+', '', text)
        return text

    norm_title = normalize(title)
    # Take first 300 characters of normalized description to avoid site-specific footers
    norm_desc = normalize(description)[:300]
    norm_price = normalize(price)

    raw_string = f"{norm_title}|{norm_desc}|{norm_price}"
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
