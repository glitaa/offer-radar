import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.infrastructure.database.orm_models import Base
from src.domain.models import Offer, SearchSession, OfferStatus, OfferUrl
from src.infrastructure.repositories.offer_repository import SQLiteOfferRepository
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

@pytest.mark.xfail(reason="Waiting for Phase 3")
@pytest.mark.asyncio
async def test_search_session_and_offer_repositories(async_session):
    session_repo = SQLiteSearchSessionRepository(async_session)
    offer_repo = SQLiteOfferRepository(async_session)
    
    session_model = SearchSession(search_url="https://olx.pl/praca/")
    await session_repo.add(session_model)
    assert session_model.id is not None
    
    fetched_session = await session_repo.get_by_url("https://olx.pl/praca/")
    assert fetched_session is not None
    assert fetched_session.id == session_model.id
    
    offer = Offer(
        fingerprint="https://olx.pl/offer-1",
        urls=[OfferUrl(url="https://olx.pl/offer-1", source="olx")],
        title="Test Job",
        session_id=session_model.id,
        price="1000 PLN",
        location="Warszawa",
        description="Test description",
        extra_data={"contract": "B2B"}
    )
    await offer_repo.add(offer)
    assert offer.id is not None
    
    fetched_offer = await offer_repo.get_by_fingerprint("https://olx.pl/offer-1")
    assert fetched_offer is not None
    assert fetched_offer.title == "Test Job"
    assert fetched_offer.status == OfferStatus.NEW
    assert fetched_offer.price == "1000 PLN"
    assert fetched_offer.location == "Warszawa"
    assert fetched_offer.description == "Test description"
    assert fetched_offer.extra_data == {"contract": "B2B"}
    
    unseen = await offer_repo.get_unseen_for_session(session_model.id)
    assert len(unseen) == 1
    assert unseen[0].id == offer.id
    
    await offer_repo.update_status(offer.id, OfferStatus.SAVED.value)
    unseen_after = await offer_repo.get_unseen_for_session(session_model.id)
    assert len(unseen_after) == 0

@pytest.mark.xfail(reason="Waiting for Phase 3")
@pytest.mark.asyncio
async def test_add_batch_ignores_duplicates(async_session):
    offer_repo = SQLiteOfferRepository(async_session)
    session_repo = SQLiteSearchSessionRepository(async_session)
    
    session_model = SearchSession(search_url="https://olx.pl/praca/")
    await session_repo.add(session_model)
    
    offer1 = Offer(
        fingerprint="https://olx.pl/offer-dup",
        urls=[OfferUrl(url="https://olx.pl/offer-dup", source="olx")],
        title="Dup Job",
        session_id=session_model.id,
        price="1",
        location="WWA",
        description="test"
    )
    await offer_repo.add(offer1)
    
    offer_dup = Offer(
        fingerprint="https://olx.pl/offer-dup",
        urls=[OfferUrl(url="https://olx.pl/offer-dup", source="olx")],
        title="Dup Job 2",
        session_id=session_model.id,
        price="2",
        location="WWA",
        description="test2"
    )
    
    offer_new = Offer(
        fingerprint="https://olx.pl/offer-new",
        urls=[OfferUrl(url="https://olx.pl/offer-new", source="olx")],
        title="New Job",
        session_id=session_model.id,
        price="100",
        location="WWA",
        description="new test"
    )
    
    await offer_repo.add_batch([offer_dup, offer_new])
    
    from sqlalchemy import select, func
    from src.infrastructure.database.orm_models import OfferORM
    stmt = select(func.count()).select_from(OfferORM)
    result = await async_session.execute(stmt)
    count = result.scalar()
    
    assert count == 2
