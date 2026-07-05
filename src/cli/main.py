import asyncio
import msvcrt
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.infrastructure.database.orm_models import Base
from src.infrastructure.repositories.search_session_repository import SQLiteSearchSessionRepository
from src.infrastructure.repositories.offer_repository import SQLiteOfferRepository
from src.application.scraper_factory import ScraperFactory
from src.application.session_manager import SessionManager
from src.application.session_manager import SessionManager
from src.domain.models import SearchSession, OfferStatus, OfferCategory

app = typer.Typer(invoke_without_command=True)
console = Console()

async def sync_with_progress(session_manager: SessionManager, session: SearchSession):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task_id = progress.add_task("[cyan]Syncing offers...", total=1)
        
        async for progress_info in session_manager.sync_offers(session.id, session.search_url):
            progress.update(
                task_id, 
                completed=progress_info.current_page, 
                total=progress_info.total_pages,
                description=f"[cyan]Syncing offers... (Found {progress_info.total_offers_found} offers so far)"
            )

async def run_loop(session_manager: SessionManager, session: SearchSession):
    while True:
        unseen_offers = await session_manager.get_unseen_offers(session.id)
        if not unseen_offers:
            console.print("[bold yellow]No new offers found.[/bold yellow]")
            break

        saved = 0
        rejected = 0
        skipped = 0
        quit_requested = False

        for offer in unseen_offers:
            snippet = offer.description[:100] + "..." if offer.description and len(offer.description) > 100 else (offer.description or "")
            
            first_url = offer.urls[0].url if offer.urls else "N/A"
            if offer.urls and len(offer.urls) > 1:
                first_url += f" (+ {len(offer.urls) - 1} other links)"

            price_label = "Salary" if offer.category == OfferCategory.JOB else "Price"
            
            price_display = "Unknown"
            if offer.price:
                if offer.price.is_free:
                    price_display = "Free"
                else:
                    min_p = offer.price.price_min
                    max_p = offer.price.price_max
                    curr = offer.price.currency or ""
                    period = f"/{offer.price.period}" if offer.price.period else ""
                    
                    if min_p is not None and max_p is not None:
                        price_display = f"{min_p} - {max_p} {curr}{period}".strip()
                    elif min_p is not None:
                        price_display = f"{min_p} {curr}{period}".strip()
                
                if offer.price.is_negotiable:
                    price_display += " (Negotiable)"

            content = (
                f"[bold]{price_label}:[/bold] {price_display}\n"
                f"[bold]Location:[/bold] {offer.location or 'N/A'}\n"
                f"[bold]URL:[/bold] {first_url}\n\n"
                f"{snippet}\n\n"
                f"[cyan](s) Save  (r) Reject  (k) Skip  (q) Quit[/cyan]"
            )
            
            console.print(Panel(content, title=f"[bold green]{offer.title}[/bold green]", expand=False))

            while True:
                key_bytes = msvcrt.getch()
                if key_bytes in (b'\x00', b'\xe0'):
                    msvcrt.getch()
                    continue
                try:
                    key = key_bytes.decode('utf-8').lower()
                except UnicodeDecodeError:
                    continue
                if key == 's':
                    await session_manager.mark_offer(offer.id, OfferStatus.SAVED)
                    saved += 1
                    break
                elif key == 'r':
                    await session_manager.mark_offer(offer.id, OfferStatus.REJECTED)
                    rejected += 1
                    break
                elif key == 'k':
                    # Skipped stays as NEW so we see it next time, but we break here to advance.
                    skipped += 1
                    break
                elif key == 'q':
                    quit_requested = True
                    break

            if quit_requested:
                break

        console.print(f"Session Summary - Saved: {saved}, Rejected: {rejected}, Skipped: {skipped}")

        if quit_requested:
            break

        console.print("Check for new results? (y/n)")
        while True:
            key_bytes = msvcrt.getch()
            if key_bytes in (b'\x00', b'\xe0'):
                msvcrt.getch()
                continue
            try:
                key = key_bytes.decode('utf-8').lower()
            except UnicodeDecodeError:
                continue
            if key == 'y':
                await sync_with_progress(session_manager, session)
                break
            elif key == 'n':
                return
            
async def main_async(url: Optional[str], query: Optional[str]):
    engine = create_async_engine("sqlite+aiosqlite:///offer_radar.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        session_repo = SQLiteSearchSessionRepository(session)
        offer_repo = SQLiteOfferRepository(session)
        scraper_factory = ScraperFactory.create_default()
        
        manager = SessionManager(session_repo, offer_repo, scraper_factory)
        
        if not url and not query:
            from src.cli.menu import run_main_menu
            await run_main_menu(manager, run_loop, sync_with_progress)
            return

        search_param = url if url else query
        console.print(f"[cyan]Starting session for: {search_param}[/cyan]")
        
        search_session = await manager.start_session(search_param)
        
        await sync_with_progress(manager, search_session)
        
        await run_loop(manager, search_session)
        
    await engine.dispose()

@app.callback()
def cli_main(
    url: Optional[str] = typer.Option(None, "--url", help="Direct URL to OLX search"),
    query: Optional[str] = typer.Option(None, "--query", help="Search query")
):
    if url and query:
        console.print("[red]Error: Please provide either --url or --query, not both.[/red]")
        raise typer.Exit(1)
    
    asyncio.run(main_async(url=url, query=query))

def main():
    app()

if __name__ == "__main__":
    main()
