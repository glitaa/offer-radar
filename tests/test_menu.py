from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import typer

from src.cli.menu import run_main_menu
from src.domain.models import SearchSession


@pytest.mark.asyncio
@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
async def test_menu_exit(mock_select, mock_print):
    mock_ask = AsyncMock()
    mock_ask.ask_async.return_value = "Exit"
    mock_select.return_value = mock_ask

    session_manager = MagicMock()
    settings_repo = MagicMock()

    with pytest.raises(typer.Exit) as exc_info:
        await run_main_menu(session_manager, settings_repo)

    assert exc_info.value.exit_code == 0
    mock_print.assert_called_with("Exiting... Goodbye!")


@pytest.mark.asyncio
@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
async def test_menu_interrupt(mock_select, mock_print):
    mock_ask = AsyncMock()
    mock_ask.ask_async.return_value = None
    mock_select.return_value = mock_ask

    session_manager = MagicMock()
    settings_repo = MagicMock()

    with pytest.raises(typer.Exit) as exc_info:
        await run_main_menu(session_manager, settings_repo)

    assert exc_info.value.exit_code == 0
    mock_print.assert_called_with("Exiting... Goodbye!")


@pytest.mark.asyncio
@patch("src.cli.menu.run_loop", new_callable=AsyncMock)
@patch("src.cli.menu.sync_with_progress", new_callable=AsyncMock)
@patch("src.cli.menu.questionary.text")
@patch("src.cli.menu.questionary.select")
async def test_menu_create_new_search(mock_select, mock_text, mock_sync, mock_run_loop):
    mock_menu_ask = AsyncMock()
    mock_menu_ask.ask_async.side_effect = ["Create new search", "Exit"]
    mock_select.return_value = mock_menu_ask

    mock_query_ask = AsyncMock()
    mock_query_ask.ask_async.return_value = "laptop"
    mock_text.return_value = mock_query_ask

    session_manager = AsyncMock()
    session = SearchSession(search_url="https://olx.pl/oferty/q-laptop/", id=1)
    session_manager.start_session.return_value = session

    settings_repo = MagicMock()

    with pytest.raises(typer.Exit):
        await run_main_menu(session_manager, settings_repo)

    session_manager.start_session.assert_called_once_with("laptop")
    mock_sync.assert_called_once_with(
        session_manager,
        session,
        active_sources=settings_repo.get_settings().active_sources,
    )
    mock_run_loop.assert_called_once_with(session_manager, session, settings_repo)


@pytest.mark.asyncio
@patch("src.cli.menu.run_loop", new_callable=AsyncMock)
@patch("src.cli.menu.sync_with_progress", new_callable=AsyncMock)
@patch("src.cli.menu.questionary.select")
async def test_menu_manage_searches_run(mock_select, mock_sync, mock_run_loop):
    session = SearchSession(search_url="https://olx.pl/oferty/q-phone/", id=42)

    mock_ask = AsyncMock()
    mock_ask.ask_async.side_effect = [
        "Manage existing searches",
        session,
        "Run search",
        "Exit",
    ]
    mock_select.return_value = mock_ask

    session_manager = AsyncMock()
    session_manager.get_all_sessions.return_value = [session]
    settings_repo = MagicMock()

    with pytest.raises(typer.Exit):
        await run_main_menu(session_manager, settings_repo)

    session_manager.get_all_sessions.assert_called_once()
    mock_sync.assert_called_once_with(
        session_manager,
        session,
        active_sources=settings_repo.get_settings().active_sources,
    )
    mock_run_loop.assert_called_once_with(session_manager, session, settings_repo)


@pytest.mark.asyncio
@patch("src.cli.menu.questionary.checkbox")
@patch("src.cli.menu.questionary.select")
async def test_settings_menu_active_sources_toggle(mock_select, mock_checkbox):
    from src.cli.menu import run_settings_menu
    from src.domain.models import Settings

    settings = Settings(active_sources=["olx"])
    settings_repo = MagicMock()
    settings_repo.get_settings.return_value = settings

    mock_select_ask = AsyncMock()
    # Choose "Active sources: OLX", then "Back"
    mock_select_ask.ask_async.side_effect = ["Active sources: OLX", "Back"]
    mock_select.return_value = mock_select_ask

    mock_checkbox_ask = AsyncMock()
    mock_checkbox_ask.ask_async.return_value = ["olx", "otodom"]
    mock_checkbox.return_value = mock_checkbox_ask

    await run_settings_menu(settings_repo, available_sources=["olx", "otodom"])

    assert settings.active_sources == ["olx", "otodom"]
    settings_repo.save_settings.assert_called_once_with(settings)
