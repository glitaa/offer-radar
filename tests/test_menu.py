import pytest
import typer
from unittest.mock import patch, MagicMock, AsyncMock
from src.cli.menu import run_main_menu

@pytest.mark.asyncio
@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
async def test_menu_exit(mock_select, mock_print):
    mock_ask = AsyncMock()
    mock_ask.ask_async.return_value = "Exit"
    mock_select.return_value = mock_ask
    
    session_manager = MagicMock()
    run_loop_cb = AsyncMock()
    sync_cb = AsyncMock()

    with pytest.raises(typer.Exit) as exc_info:
        await run_main_menu(session_manager, run_loop_cb, sync_cb)

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
    run_loop_cb = AsyncMock()
    sync_cb = AsyncMock()

    with pytest.raises(typer.Exit) as exc_info:
        await run_main_menu(session_manager, run_loop_cb, sync_cb)

    assert exc_info.value.exit_code == 0
    mock_print.assert_called_with("Exiting... Goodbye!")

@pytest.mark.asyncio
@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
async def test_menu_placeholder(mock_select, mock_print):
    mock_ask = AsyncMock()
    mock_ask.ask_async.side_effect = ["Settings", "Exit"]
    mock_select.return_value = mock_ask
    
    session_manager = MagicMock()
    run_loop_cb = AsyncMock()
    sync_cb = AsyncMock()

    with pytest.raises(typer.Exit) as exc_info:
        await run_main_menu(session_manager, run_loop_cb, sync_cb)

    assert exc_info.value.exit_code == 0
    mock_print.assert_any_call("[yellow]'Settings' is not implemented yet.[/yellow]")
    mock_print.assert_any_call("Exiting... Goodbye!")
