import typer
import questionary
from rich.console import Console
import builtins

_ = lambda x: getattr(builtins, '_', lambda s: s)(x)
console = Console()

async def run_settings_menu(settings_repo):
    while True:
        settings = settings_repo.get_settings()
        lang_display = _("English") if settings.language == "en" else _("Polish") if settings.language == "pl" else settings.language
        lang_text = _("Language: {lang}").format(lang=lang_display)
        auto_display = _("On") if settings.auto_open_browser else _("Off")
        browser_text = _("Auto-open browser: {auto}").format(auto=auto_display)
        back_text = _("Back")
        
        choice = await questionary.select(
            _("Settings Menu"),
            instruction=_("(Use arrow keys)"),
            choices=[
                lang_text,
                browser_text,
                back_text
            ]
        ).ask_async(kbi_msg=_("\nCancelled by user\n"))
        
        if choice == back_text or choice is None:
            break
            
        elif choice == lang_text:
            choice_en = _("English")
            choice_pl = _("Polish")
            new_lang_choice = await questionary.select(
                _("Select language"),
                instruction=_("(Use arrow keys)"),
                choices=[choice_en, choice_pl]
            ).ask_async(kbi_msg=_("\nCancelled by user\n"))
            if new_lang_choice:
                new_lang = "en" if new_lang_choice == choice_en else "pl"
                settings.language = new_lang
                try:
                    settings_repo.save_settings(settings)
                    from src.cli.i18n import setup_i18n
                    builtins._ = setup_i18n(new_lang)
                except Exception as e:
                    console.print(f"[red]{_('Error saving settings')}: {e}[/red]")
                    
        elif choice == browser_text:
            choice_on = _("On")
            choice_off = _("Off")
            new_val = await questionary.select(
                _("Auto-open browser when showing offers?"),
                instruction=_("(Use arrow keys)"),
                choices=[choice_on, choice_off]
            ).ask_async(kbi_msg=_("\nCancelled by user\n"))
            if new_val:
                settings.auto_open_browser = (new_val == choice_on)
                try:
                    settings_repo.save_settings(settings)
                except Exception as e:
                    console.print(f"[red]{_('Error saving settings')}: {e}[/red]")

async def run_main_menu(session_manager, run_loop_cb, sync_cb, settings_repo):
    while True:
        choice = await questionary.select(
            _("Offer-Radar"),
            instruction=_("(Use arrow keys)"),
            choices=[
                _("Create new search"),
                _("Manage existing searches"),
                _("Settings"),
                _("Exit")
            ]
        ).ask_async(kbi_msg=_("\nCancelled by user\n"))

        if choice == _("Exit") or choice is None:
            console.print(_("Exiting... Goodbye!"))
            raise typer.Exit(0)
            
        elif choice == _("Create new search"):
            query = await questionary.text(_("Enter a search query or URL:")).ask_async(kbi_msg=_("\nCancelled by user\n"))
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
                instruction=_("(Use arrow keys)"),
                choices=choices
            ).ask_async(kbi_msg=_("\nCancelled by user\n"))
            
            if selected_session == "back" or selected_session is None:
                continue
                
            action = await questionary.select(
                _("Manage '{name}'").format(name=selected_session.display_name),
                instruction=_("(Use arrow keys)"),
                choices=[_("Run search"), _("Delete search"), _("Back")]
            ).ask_async(kbi_msg=_("\nCancelled by user\n"))
            
            if action == _("Run search"):
                console.print(_("[cyan]Running session: {name}[/cyan]").format(name=selected_session.display_name))
                await sync_cb(session_manager, selected_session)
                await run_loop_cb(session_manager, selected_session, settings_repo)
                
            elif action == _("Delete search"):
                count = await session_manager.count_offers_for_session(selected_session.id)
                confirm = await questionary.confirm(
                    _("Are you sure? This will delete the session '{name}' and {count} linked offers.").format(name=selected_session.display_name, count=count)
                ).ask_async(kbi_msg=_("\nCancelled by user\n"))
                
                if confirm:
                    await session_manager.delete_session(selected_session.id)
                    console.print(_("[green]Session '{name}' deleted.[/green]").format(name=selected_session.display_name))
                    
        elif choice == _("Settings"):
            await run_settings_menu(settings_repo)
            
        else:
            console.print(_("[yellow]'{choice}' is not implemented yet.[/yellow]").format(choice=choice))
