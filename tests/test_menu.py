import pytest
import typer
from unittest.mock import patch, MagicMock
from src.cli.menu import run_main_menu

@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
def test_menu_exit(mock_select, mock_print):
    mock_ask = MagicMock()
    mock_ask.ask.return_value = "Exit"
    mock_select.return_value = mock_ask

    with pytest.raises(typer.Exit) as exc_info:
        run_main_menu()

    assert exc_info.value.exit_code == 0
    mock_print.assert_called_with("Exiting... Goodbye!")

@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
def test_menu_interrupt(mock_select, mock_print):
    mock_ask = MagicMock()
    mock_ask.ask.return_value = None
    mock_select.return_value = mock_ask

    with pytest.raises(typer.Exit) as exc_info:
        run_main_menu()

    assert exc_info.value.exit_code == 0
    mock_print.assert_called_with("Exiting... Goodbye!")

@patch("src.cli.menu.console.print")
@patch("src.cli.menu.questionary.select")
def test_menu_placeholder(mock_select, mock_print):
    mock_ask = MagicMock()
    mock_ask.ask.side_effect = ["Settings", "Exit"]
    mock_select.return_value = mock_ask

    with pytest.raises(typer.Exit) as exc_info:
        run_main_menu()

    assert exc_info.value.exit_code == 0
    mock_print.assert_any_call("[yellow]'Settings' is not implemented yet.[/yellow]")
    mock_print.assert_any_call("Exiting... Goodbye!")
