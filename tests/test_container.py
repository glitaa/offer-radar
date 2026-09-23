import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from src.application.session_manager import SessionManager
from src.container import AppContainer, create_app_container
from src.domain.interfaces import SettingsRepository
from src.infrastructure.database.orm_models import Base
from src.infrastructure.repositories.toml_settings_repository import (
    TOMLSettingsRepository,
)


@pytest.mark.asyncio
async def test_create_app_container_wires_dependencies_cleanly(tmp_path):
    test_db = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db.as_posix()}", echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    settings_file = tmp_path / "config.toml"
    settings_repo = TOMLSettingsRepository(str(settings_file))

    async with create_app_container(
        engine=engine, settings_repo=settings_repo
    ) as container:
        assert isinstance(container, AppContainer)
        assert isinstance(container.session_manager, SessionManager)
        assert isinstance(container.settings_repo, SettingsRepository)

        # Verify operational database connectivity and use-case execution
        session = await container.session_manager.start_session(
            "https://www.olx.pl/oferty/q-laptop/"
        )
        assert session.id is not None

        all_sessions = await container.session_manager.get_all_sessions()
        assert len(all_sessions) == 1
        assert all_sessions[0].id == session.id

    await engine.dispose()
