import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

class OfferStatus(str, Enum):
    NEW = "New"
    SAVED = "Saved"
    REJECTED = "Rejected"
    SKIPPED = "Skipped"

class OfferCategory(str, Enum):
    JOB = "JOB"
    REAL_ESTATE = "REAL_ESTATE"

@dataclass
class OfferPrice:
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    special_status: Optional[str] = None
    is_free: bool = False
    is_negotiable: bool = False

@dataclass
class OfferUrl:
    url: str

@dataclass
class Offer:
    title: str
    status: OfferStatus = OfferStatus.NEW
    id: Optional[int] = None
    session_id: Optional[int] = None
    price: Optional[OfferPrice] = None
    location: Optional[str] = None
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    urls: List[OfferUrl] = field(default_factory=list)
    fingerprint: str = ""
    category: Optional[OfferCategory] = None

    def __post_init__(self):
        if self.fingerprint == "":
            self.fingerprint = self.compute_fingerprint()

    def compute_fingerprint(self) -> str:
        price_str = ""
        if self.price is not None:
            p_parts = [
                str(self.price.price_min) if self.price.price_min is not None else "",
                str(self.price.price_max) if self.price.price_max is not None else "",
                str(self.price.currency) if self.price.currency is not None else "",
                str(self.price.period) if self.price.period is not None else "",
                str(self.price.special_status) if self.price.special_status is not None else "",
                str(self.price.is_free),
                str(self.price.is_negotiable)
            ]
            price_str = " ".join(p_parts)
            
        desc_str = self.description if self.description is not None else ""
        cat_str = self.category.value if self.category is not None else ""
        raw = f"{self.title} {desc_str} {price_str} {cat_str}"
        
        # Normalize: lowercase
        norm = raw.lower()
        # Remove punctuation
        norm = re.sub(r'[^\w\s]', '', norm)
        # Collapse whitespace
        norm = re.sub(r'\s+', ' ', norm).strip()
        
        return hashlib.sha256(norm.encode('utf-8')).hexdigest()

@dataclass
class SearchSession:
    search_url: str
    id: Optional[int] = None

@dataclass
class SyncProgress:
    current_page: int
    total_pages: int
    total_offers_found: int
