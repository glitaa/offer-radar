from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

class ListingStatus(str, Enum):
    NEW = "New"
    SAVED = "Saved"
    REJECTED = "Rejected"
    SKIPPED = "Skipped"

@dataclass
class Listing:
    url: str
    title: str
    status: ListingStatus = ListingStatus.NEW
    id: Optional[int] = None
    session_id: Optional[int] = None
    price: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

@dataclass
class SearchSession:
    search_url: str
    id: Optional[int] = None
