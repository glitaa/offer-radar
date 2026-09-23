from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()


class SearchSessionORM(Base):
    __tablename__ = "search_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_url: Mapped[str] = mapped_column(String, unique=True, index=True)
    query: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    offers: Mapped[list["OfferORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


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
    extra_data: Mapped[str | None] = mapped_column(String, nullable=True)

    urls: Mapped[list["OfferUrlORM"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan", lazy="selectin"
    )


class OfferUrlORM(Base):
    __tablename__ = "offer_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"))
    url: Mapped[str] = mapped_column(String, unique=True, index=True)

    offer: Mapped["OfferORM"] = relationship(back_populates="urls")
