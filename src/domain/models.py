import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    price_min: float | None = None
    price_max: float | None = None
    currency: str | None = None
    period: str | None = None
    special_status: str | None = None
    is_free: bool = False
    is_negotiable: bool = False


@dataclass
class OfferUrl:
    url: str


@dataclass
class Offer:
    title: str
    status: OfferStatus = OfferStatus.NEW
    id: int | None = None
    session_id: int | None = None
    price: OfferPrice | None = None
    location: str | None = None
    description: str | None = None
    extra_data: dict[str, Any] | None = None
    urls: list[OfferUrl] = field(default_factory=list)
    fingerprint: str = ""
    category: OfferCategory | None = None
    source: str = "olx"

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
                str(self.price.special_status)
                if self.price.special_status is not None
                else "",
                str(self.price.is_free),
                str(self.price.is_negotiable),
            ]
            price_str = " ".join(p_parts)

        desc_str = self.description if self.description is not None else ""
        cat_str = self.category.value if self.category is not None else ""
        raw = f"{self.title} {desc_str} {price_str} {cat_str}"

        # Normalize: lowercase
        norm = raw.lower()
        # Remove punctuation
        norm = re.sub(r"[^\w\s]", "", norm)
        # Collapse whitespace
        norm = re.sub(r"\s+", " ", norm).strip()

        return hashlib.sha256(norm.encode("utf-8")).hexdigest()


@dataclass
class SearchSession:
    search_url: str
    id: int | None = None
    query: str | None = None

    @property
    def display_name(self) -> str:
        if self.query:
            return self.query
        import re
        import urllib.parse

        match = re.search(r"q-([^/?]+)", self.search_url)
        if match:
            raw_query = urllib.parse.unquote(match.group(1))
            return raw_query.replace("-", " ")
        return self.search_url


@dataclass
class SyncProgress:
    current_page: int
    total_pages: int
    total_offers_found: int


@dataclass
class Settings:
    language: str = "en"
    auto_open_browser: bool = True
    active_sources: list[str] = field(default_factory=lambda: ["olx"])
