from dataclasses import dataclass
from enum import Enum
from typing import Optional

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

@dataclass
class SearchSession:
    search_url: str
    id: Optional[int] = None
