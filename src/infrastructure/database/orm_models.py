from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from src.domain.models import (
    Offer,
    OfferCategory,
    OfferPrice,
    OfferStatus,
    OfferUrl,
    SearchSession,
)

Base = declarative_base()


class SearchSessionORM(Base):
    __tablename__ = "search_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_url: Mapped[str] = mapped_column(String, unique=True, index=True)
    query: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    offers: Mapped[list["OfferORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    @classmethod
    def from_domain(cls, session: SearchSession) -> "SearchSessionORM":
        return cls(id=session.id, search_url=session.search_url, query=session.query)

    def to_domain(self) -> SearchSession:
        return SearchSession(id=self.id, search_url=self.search_url, query=self.query)


class OfferORM(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("search_sessions.id"))
    source: Mapped[str | None] = mapped_column(String, nullable=True, default="olx")

    session: Mapped["SearchSessionORM"] = relationship(back_populates="offers")
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String, nullable=True)
    period: Mapped[str | None] = mapped_column(String, nullable=True)
    special_status: Mapped[str | None] = mapped_column(String, nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    urls: Mapped[list["OfferUrlORM"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan", lazy="selectin"
    )

    @classmethod
    def from_domain(cls, offer: Offer) -> "OfferORM":
        price = offer.price
        return cls(
            id=offer.id,
            fingerprint=offer.fingerprint,
            title=offer.title,
            status=offer.status.value,
            session_id=offer.session_id,
            source=offer.source or "olx",
            price_min=price.price_min if price else None,
            price_max=price.price_max if price else None,
            currency=price.currency if price else None,
            period=price.period if price else None,
            special_status=price.special_status if price else None,
            is_free=price.is_free if price else False,
            is_negotiable=price.is_negotiable if price else False,
            category=offer.category.value if offer.category else None,
            location=offer.location,
            description=offer.description,
            extra_data=offer.extra_data,
            urls=[OfferUrlORM(url=u.url) for u in offer.urls],
        )

    def to_domain(self) -> Offer:
        has_price = any(
            [
                self.price_min is not None,
                self.price_max is not None,
                self.currency is not None,
                self.period is not None,
                self.special_status is not None,
                self.is_free,
                self.is_negotiable,
            ]
        )
        price = (
            OfferPrice(
                price_min=self.price_min,
                price_max=self.price_max,
                currency=self.currency,
                period=self.period,
                special_status=self.special_status,
                is_free=self.is_free,
                is_negotiable=self.is_negotiable,
            )
            if has_price
            else None
        )
        return Offer(
            id=self.id,
            fingerprint=self.fingerprint,
            title=self.title,
            status=OfferStatus(self.status),
            session_id=self.session_id,
            price=price,
            location=self.location,
            description=self.description,
            extra_data=self.extra_data,
            urls=[OfferUrl(url=u.url) for u in self.urls],
            category=OfferCategory(self.category) if self.category else None,
            source=self.source or "olx",
        )


class OfferUrlORM(Base):
    __tablename__ = "offer_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"))
    url: Mapped[str] = mapped_column(String, unique=True, index=True)

    offer: Mapped["OfferORM"] = relationship(back_populates="urls")
