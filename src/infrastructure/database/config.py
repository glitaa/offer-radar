from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.database.orm_models import Base

DATA_DIR = Path("data")
DEFAULT_DB_PATH = DATA_DIR / "offer_radar.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}"


def ensure_data_dir(target_dir: Path = DATA_DIR) -> Path:
    """Ensure the database directory exists."""
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def get_engine(url: str | None = None) -> AsyncEngine:
    """Create and return an AsyncEngine, ensuring the parent directory exists if using SQLite."""
    db_url = url or DEFAULT_DATABASE_URL
    if "sqlite" in db_url and not db_url.endswith(":memory:"):
        prefix = "sqlite+aiosqlite:///"
        if db_url.startswith(prefix):
            raw_path = db_url[len(prefix) :]
            parent = Path(raw_path).parent
            if str(parent) not in ("", "."):
                parent.mkdir(parents=True, exist_ok=True)
            else:
                ensure_data_dir()
        else:
            ensure_data_dir()
    return create_async_engine(db_url, echo=False)


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create and return an async sessionmaker."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database schema by creating all registered tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
