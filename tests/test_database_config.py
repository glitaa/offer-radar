import pytest
from pathlib import Path
from src.infrastructure.database.config import (
    ensure_data_dir,
    get_engine,
    get_session_factory,
    init_db,
)


def test_ensure_data_dir_creates_missing_directory(tmp_path: Path):
    target_dir = tmp_path / "nested" / "data"
    assert not target_dir.exists()

    result = ensure_data_dir(target_dir)
    assert target_dir.exists()
    assert result == target_dir


def test_get_engine_creates_directory_for_sqlite_path(tmp_path: Path):
    test_db_dir = tmp_path / "custom_data"
    db_file = test_db_dir / "test.db"
    assert not test_db_dir.exists()

    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = get_engine(url)
    assert engine is not None
    assert test_db_dir.exists()


@pytest.mark.asyncio
async def test_init_db_and_session_factory(tmp_path: Path):
    db_file = tmp_path / "test_init.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = get_engine(url)

    await init_db(engine)

    session_maker = get_session_factory(engine)
    async with session_maker() as session:
        assert session is not None

    await engine.dispose()
