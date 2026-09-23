import asyncio
import builtins

import typer
from rich.console import Console

from src.cli.i18n import setup_i18n
from src.cli.menu import run_main_menu
from src.cli.review import run_loop, sync_with_progress
from src.container import create_app_container

__all__ = ["app", "cli_main", "main", "main_async", "run_loop", "sync_with_progress"]

app = typer.Typer(invoke_without_command=True)
console = Console()


def _(x: str) -> str:
    return getattr(builtins, "_", lambda s: s)(x)


async def main_async(url: str | None, query: str | None) -> None:
    async with create_app_container() as container:
        settings = container.settings_repo.get_settings()
        builtins._ = setup_i18n(settings.language)

        if not url and not query:
            await run_main_menu(container.session_manager, container.settings_repo)
            return

        search_param = url if url else query
        console.print(
            _("Starting session for: {search_param}").format(search_param=search_param)
        )

        search_session = await container.session_manager.start_session(search_param)
        await sync_with_progress(
            container.session_manager,
            search_session,
            active_sources=settings.active_sources,
        )
        await run_loop(
            container.session_manager, search_session, container.settings_repo
        )


@app.callback()
def cli_main(
    url: str | None = typer.Option(None, "--url", help="Direct URL to OLX search"),
    query: str | None = typer.Option(None, "--query", help="Search query"),
):
    if url and query:
        console.print(
            _("[red]Error: Please provide either --url or --query, not both.[/red]")
        )
        raise typer.Exit(1)

    asyncio.run(main_async(url=url, query=query))


def main():
    app()


if __name__ == "__main__":
    main()
