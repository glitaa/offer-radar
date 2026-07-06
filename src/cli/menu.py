import typer
import questionary
from rich.console import Console
import builtins

_ = getattr(builtins, '_', lambda x: x)
console = Console()

async def run_settings_menu(settings_repo):
    while True:
        settings = settings_repo.get_settings()
        lang_text = _("Language (Current: {lang})").format(lang=settings.language)
        browser_text = _("Auto-open browser (Current: {auto})").format(auto=settings.auto_open_browser)
        back_text = _("Back")
        
        choice = await questionary.select(
            _("Settings Menu"),
            choices=[
                lang_text,
                browser_text,
                back_text
            ]
        ).ask_async()
        
        if choice == back_text or choice is None:
            break
            
        elif choice == lang_text:
            new_lang = await questionary.select(
                _("Select language"),
                choices=["en", "pl"]
            ).ask_async()
            if new_lang:
                settings.language = new_lang
                try:
                    settings_repo.save_settings(settings)
                except Exception as e:
                    console.print(f"[red]{_('Error saving settings')}: {e}[/red]")
                    
        elif choice == browser_text:
            new_val = await questionary.select(
                _("Auto-open browser when showing offers?"),
                choices=["True", "False"]
            ).ask_async()
            if new_val:
                settings.auto_open_browser = (new_val == "True")
                try:
                    settings_repo.save_settings(settings)
                except Exception as e:
                    console.print(f"[red]{_('Error saving settings')}: {e}[/red]")

async def run_main_menu(session_manager, run_loop_cb, sync_cb, settings_repo):
    while True:
        choice = await questionary.select(
            _("Offer-Radar Main Menu"),
            choices=[
                _("Create new search"),
                _("Manage existing searches"),
                _("Settings"),
                _("Exit")
            ]
        ).ask_async()

        if choice == _("Exit") or choice is None:
            console.print(_("Exiting... Goodbye!"))
            raise typer.Exit(0)
            
        elif choice == _("Create new search"):
            query = await questionary.text(_("Enter a search query or URL:")).ask_async()
            if not query:
                continue
                
            session = await session_manager.start_session(query)
            console.print(_("[cyan]Started session for: {name}[/cyan]").format(name=session.display_name))
            await sync_cb(session_manager, session)
            await run_loop_cb(session_manager, session, settings_repo)

        elif choice == _("Manage existing searches"):
            sessions = await session_manager.get_all_sessions()
            if not sessions:
                console.print(_("[yellow]No existing searches found.[/yellow]"))
                continue
                
            choices = [questionary.Choice(s.display_name, value=s) for s in sessions]
            choices.append(questionary.Choice(_("Back"), value="back"))
            
            selected_session = await questionary.select(
                _("Select a search to manage"),
                choices=choices
            ).ask_async()
            
            if selected_session == "back" or selected_session is None:
                continue
                
            action = await questionary.select(
                _("Manage '{name}'").format(name=selected_session.display_name),
                choices=[_("Run search"), _("Delete search"), _("Back")]
            ).ask_async()
            
            if action == _("Run search"):
                console.print(_("[cyan]Running session: {name}[/cyan]").format(name=selected_session.display_name))
                await sync_cb(session_manager, selected_session)
                await run_loop_cb(session_manager, selected_session, settings_repo)
                
            elif action == _("Delete search"):
                count = await session_manager.count_offers_for_session(selected_session.id)
                confirm = await questionary.confirm(
                    _("Are you sure? This will delete the session '{name}' and {count} linked offers.").format(name=selected_session.display_name, count=count)
                ).ask_async()
                
                if confirm:
                    await session_manager.delete_session(selected_session.id)
                    console.print(_("[green]Session '{name}' deleted.[/green]").format(name=selected_session.display_name))
                    
        elif choice == _("Settings"):
            await run_settings_menu(settings_repo)
            
        else:
            console.print(_("[yellow]'{choice}' is not implemented yet.[/yellow]").format(choice=choice))
