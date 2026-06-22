from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

class OfferStatus(str, Enum):
    NEW = "New"
    SAVED = "Saved"
    REJECTED = "Rejected"
    SKIPPED = "Skipped"

@dataclass
class OfferUrl:
    url: str
    source: str = "olx"

@dataclass
class Offer:
    title: str
    fingerprint: str
    status: OfferStatus = OfferStatus.NEW
    id: Optional[int] = None
    session_id: Optional[int] = None
    price: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    urls: List[OfferUrl] = field(default_factory=list)

@dataclass
class SearchSession:
    search_url: str
    id: Optional[int] = None
