import typer
import questionary
from rich.console import Console

console = Console()

async def run_main_menu(session_manager, run_loop_cb, sync_cb):
    while True:
        choice = await questionary.select(
            "Offer-Radar Main Menu",
            choices=[
                "Create new search",
                "Manage existing searches",
                "Settings",
                "Exit"
            ]
        ).ask_async()

        if choice == "Exit" or choice is None:
            console.print("Exiting... Goodbye!")
            raise typer.Exit(0)
            
        elif choice == "Create new search":
            query = await questionary.text("Enter a search query or URL:").ask_async()
            if not query:
                continue
                
            session = await session_manager.start_session(query)
            console.print(f"[cyan]Started session for: {session.display_name}[/cyan]")
            await sync_cb(session_manager, session)
            await run_loop_cb(session_manager, session)

        elif choice == "Manage existing searches":
            sessions = await session_manager.get_all_sessions()
            if not sessions:
                console.print("[yellow]No existing searches found.[/yellow]")
                continue
                
            choices = [questionary.Choice(s.display_name, value=s) for s in sessions]
            choices.append(questionary.Choice("Back", value="back"))
            
            selected_session = await questionary.select(
                "Select a search to manage",
                choices=choices
            ).ask_async()
            
            if selected_session == "back" or selected_session is None:
                continue
                
            action = await questionary.select(
                f"Manage '{selected_session.display_name}'",
                choices=["Run search", "Delete search", "Back"]
            ).ask_async()
            
            if action == "Run search":
                console.print(f"[cyan]Running session: {selected_session.display_name}[/cyan]")
                await sync_cb(session_manager, selected_session)
                await run_loop_cb(session_manager, selected_session)
                
            elif action == "Delete search":
                count = await session_manager.count_offers_for_session(selected_session.id)
                confirm = await questionary.confirm(
                    f"Are you sure? This will delete the session '{selected_session.display_name}' and {count} linked offers."
                ).ask_async()
                
                if confirm:
                    await session_manager.delete_session(selected_session.id)
                    console.print(f"[green]Session '{selected_session.display_name}' deleted.[/green]")
        else:
            console.print(f"[yellow]'{choice}' is not implemented yet.[/yellow]")
