import typer
import questionary
from rich.console import Console

console = Console()

def run_main_menu():
    while True:
        choice = questionary.select(
            "Offer-Radar Main Menu",
            choices=[
                "Create new search",
                "Manage existing searches",
                "Settings",
                "Exit"
            ]
        ).ask()

        if choice == "Exit" or choice is None:
            console.print("Exiting... Goodbye!")
            raise typer.Exit(0)
        else:
            console.print(f"[yellow]'{choice}' is not implemented yet.[/yellow]")
