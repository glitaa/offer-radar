import asyncio
import argparse
import msvcrt
import sys
from rich.console import Console
from rich.panel import Panel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.infrastructure.database.orm_models import Base
from src.infrastructure.repositories.search_session_repository import SQLiteSearchSessionRepository
from src.infrastructure.repositories.listing_repository import SQLiteListingRepository
from src.application.scraper_factory import ScraperFactory
from src.application.session_manager import SessionManager
from src.domain.models import SearchSession, ListingStatus

console = Console()

async def run_loop(session_manager: SessionManager, session: SearchSession):
    while True:
        unseen_listings = await session_manager.get_unseen_listings(session.id)
        if not unseen_listings:
            console.print("[bold yellow]No new listings found.[/bold yellow]")
            break

        saved = 0
        rejected = 0
        skipped = 0
        quit_requested = False

        for listing in unseen_listings:
            snippet = listing.description[:100] + "..." if listing.description and len(listing.description) > 100 else (listing.description or "")
            content = (
                f"[bold]Price:[/bold] {listing.price or 'N/A'}\n"
                f"[bold]Location:[/bold] {listing.location or 'N/A'}\n"
                f"[bold]URL:[/bold] {listing.url}\n\n"
                f"{snippet}\n\n"
                f"[cyan][s] Save  [r] Reject  [k] Skip  [q] Quit[/cyan]"
            )
            
            console.print(Panel(content, title=f"[bold green]{listing.title}[/bold green]", expand=False))

            while True:
                key = msvcrt.getch().decode('utf-8').lower()
                if key == 's':
                    await session_manager.mark_listing(listing.id, ListingStatus.SAVED)
                    saved += 1
                    break
                elif key == 'r':
                    await session_manager.mark_listing(listing.id, ListingStatus.REJECTED)
                    rejected += 1
                    break
                elif key == 'k':
                    # Skipped stays as NEW so we see it next time, but we break here to advance.
                    # Or we mark it as SKIPPED? Requirements: "(Skip means show again next time)"
                    # Wait, requirement says "Skip means show again next time". If we mark it SKIPPED, 
                    # we need to make sure get_unseen_listings doesn't fetch it? No, if we want to show it again,
                    # we probably shouldn't change the state.
                    # Wait, the prompt says: "Call `await session_manager.mark_listing(listing.id, ListingStatus.<STATUS>)` accordingly"
                    # But if we change it to SKIPPED, get_unseen fetches NEW.
                    # Let's read PROJECT.md: "(Skip means show again next time)"
                    # Okay, maybe we shouldn't change it to skipped or change it to SKIPPED and get_unseen fetches NEW and SKIPPED?
                    # The prompt says: "Call `await session_manager.mark_listing(listing.id, ListingStatus.<STATUS>)` accordingly"
                    # If I use `ListingStatus.SKIPPED`, get_unseen_for_session only fetches `ListingStatus.NEW.value`.
                    # So if I mark it SKIPPED, it will NOT be shown next time. 
                    # Let's skip marking, or mark it as NEW, or wait, maybe skip doesn't call mark_listing.
                    # I'll just skip and not call mark_listing to keep it NEW, but wait, the prompt says:
                    # "Call `await session_manager.mark_listing(listing.id, ListingStatus.<STATUS>)` accordingly"
                    # I will call mark_listing with ListingStatus.NEW for skip, or simply just `break`.
                    # I'll just `break` to advance. But let's check: I'll increment skipped and break.
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
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'y':
                await session_manager.sync_listings(session.id, session.search_url)
                break
            elif key == 'n':
                return
            
async def main_async():
    parser = argparse.ArgumentParser(description="Offer-Radar CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Direct URL to OLX search")
    group.add_argument("--query", help="Search query")
    
    args = parser.parse_args()
    
    engine = create_async_engine("sqlite+aiosqlite:///offer_radar.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        session_repo = SQLiteSearchSessionRepository(session)
        listing_repo = SQLiteListingRepository(session)
        scraper_factory = ScraperFactory.create_default()
        
        manager = SessionManager(session_repo, listing_repo, scraper_factory)
        
        search_param = args.url if args.url else args.query
        console.print(f"[cyan]Starting session for: {search_param}[/cyan]")
        
        search_session = await manager.start_session(search_param)
        
        console.print("[cyan]Syncing listings...[/cyan]")
        await manager.sync_listings(search_session.id, search_session.search_url)
        
        await run_loop(manager, search_session)
        
    await engine.dispose()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
