from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from src.application.session_manager import SessionManager
from src.domain.interfaces import SettingsRepository
from src.infrastructure.database.config import (
    get_engine,
    get_session_factory,
    init_db,
)
from src.infrastructure.repositories.offer_repository import SQLiteOfferRepository
from src.infrastructure.repositories.search_session_repository import (
    SQLiteSearchSessionRepository,
)
from src.infrastructure.repositories.toml_settings_repository import (
    TOMLSettingsRepository,
)
from src.infrastructure.scrapers.factory import create_default_scraper_factory


@dataclass
class AppContainer:
    """Composition container providing assembled application services and settings."""

    session_manager: SessionManager
    settings_repo: SettingsRepository
    engine: AsyncEngine


@asynccontextmanager
async def create_app_container(
    engine: AsyncEngine | None = None,
    settings_repo: SettingsRepository | None = None,
) -> AsyncGenerator[AppContainer]:
    """Assemble application services and dependencies within a managed lifecycle.

    If no engine is provided, creates and initializes the default database engine,
    and disposes it upon exit.
    """
    dispose_engine = False
    if engine is None:
        engine = get_engine()
        await init_db(engine)
        dispose_engine = True

    if settings_repo is None:
        settings_repo = TOMLSettingsRepository()

    session_factory = get_session_factory(engine)
    async with session_factory() as session:
        session_repo = SQLiteSearchSessionRepository(session)
        offer_repo = SQLiteOfferRepository(session)
        scraper_factory = create_default_scraper_factory()
        session_manager = SessionManager(session_repo, offer_repo, scraper_factory)

        yield AppContainer(
            session_manager=session_manager,
            settings_repo=settings_repo,
            engine=engine,
        )

    if dispose_engine:
        await engine.dispose()
