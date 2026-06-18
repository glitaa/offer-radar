import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.infrastructure.database.orm_models import Base
from src.domain.models import Listing, SearchSession, ListingStatus
from src.infrastructure.repositories.listing_repository import SQLiteListingRepository
from src.infrastructure.repositories.search_session_repository import SQLiteSearchSessionRepository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_search_session_and_listing_repositories(async_session):
    session_repo = SQLiteSearchSessionRepository(async_session)
    listing_repo = SQLiteListingRepository(async_session)
    
    session_model = SearchSession(search_url="https://olx.pl/praca/")
    await session_repo.add(session_model)
    assert session_model.id is not None
    
    fetched_session = await session_repo.get_by_url("https://olx.pl/praca/")
    assert fetched_session is not None
    assert fetched_session.id == session_model.id
    
    listing = Listing(
        url="https://olx.pl/offer-1",
        title="Test Job",
        session_id=session_model.id
    )
    await listing_repo.add(listing)
    assert listing.id is not None
    
    fetched_listing = await listing_repo.get_by_url("https://olx.pl/offer-1")
    assert fetched_listing is not None
    assert fetched_listing.title == "Test Job"
    assert fetched_listing.status == ListingStatus.NEW
    
    unseen = await listing_repo.get_unseen_for_session(session_model.id)
    assert len(unseen) == 1
    assert unseen[0].id == listing.id
    
    await listing_repo.update_status(listing.id, ListingStatus.SAVED.value)
    unseen_after = await listing_repo.get_unseen_for_session(session_model.id)
    assert len(unseen_after) == 0
