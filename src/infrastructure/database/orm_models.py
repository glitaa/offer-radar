from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from typing import Optional, List

Base = declarative_base()

class SearchSessionORM(Base):
    __tablename__ = "search_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_url: Mapped[str] = mapped_column(String, unique=True, index=True)

class OfferORM(Base):
    __tablename__ = "offers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("search_sessions.id"))
    price: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    urls: Mapped[List["OfferUrlORM"]] = relationship(back_populates="offer", cascade="all, delete-orphan", lazy="selectin")

class OfferUrlORM(Base):
    __tablename__ = "offer_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"))
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[str] = mapped_column(String)
    
    offer: Mapped["OfferORM"] = relationship(back_populates="urls")
