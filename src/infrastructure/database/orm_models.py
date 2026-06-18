from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey

Base = declarative_base()

class SearchSessionORM(Base):
    __tablename__ = "search_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_url: Mapped[str] = mapped_column(String, unique=True, index=True)

class ListingORM(Base):
    __tablename__ = "listings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("search_sessions.id"))
