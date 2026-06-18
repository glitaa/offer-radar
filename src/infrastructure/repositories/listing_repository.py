from src.domain.interfaces import ListingRepository
from src.domain.models import Listing, ListingStatus
from src.infrastructure.database.orm_models import ListingORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json

class SQLiteListingRepository(ListingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, listing: Listing) -> None:
        extra_data_json = json.dumps(listing.extra_data) if listing.extra_data else None
        orm_model = ListingORM(
            url=listing.url,
            title=listing.title,
            status=listing.status.value,
            session_id=listing.session_id,
            price=listing.price,
            location=listing.location,
            description=listing.description,
            extra_data=extra_data_json
        )
        self.session.add(orm_model)
        await self.session.commit()
        listing.id = orm_model.id

    async def add_batch(self, listings: List[Listing]) -> None:
        orm_models = []
        for listing in listings:
            extra_data_json = json.dumps(listing.extra_data) if listing.extra_data else None
            orm_model = ListingORM(
                url=listing.url,
                title=listing.title,
                status=listing.status.value,
                session_id=listing.session_id,
                price=listing.price,
                location=listing.location,
                description=listing.description,
                extra_data=extra_data_json
            )
            orm_models.append((listing, orm_model))
            self.session.add(orm_model)
            
        await self.session.commit()
        for listing, orm_model in orm_models:
            listing.id = orm_model.id
        
    async def get_by_url(self, url: str) -> Optional[Listing]:
        stmt = select(ListingORM).where(ListingORM.url == url)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            extra_data = json.loads(orm_model.extra_data) if orm_model.extra_data else None
            return Listing(
                id=orm_model.id,
                url=orm_model.url,
                title=orm_model.title,
                status=ListingStatus(orm_model.status),
                session_id=orm_model.session_id,
                price=orm_model.price,
                location=orm_model.location,
                description=orm_model.description,
                extra_data=extra_data
            )
        return None

    async def get_unseen_for_session(self, session_id: int) -> List[Listing]:
        stmt = select(ListingORM).where(
            ListingORM.session_id == session_id,
            ListingORM.status == ListingStatus.NEW.value
        )
        result = await self.session.execute(stmt)
        orm_models = result.scalars().all()
        
        return [
            Listing(
                id=orm_model.id,
                url=orm_model.url,
                title=orm_model.title,
                status=ListingStatus(orm_model.status),
                session_id=orm_model.session_id,
                price=orm_model.price,
                location=orm_model.location,
                description=orm_model.description,
                extra_data=json.loads(orm_model.extra_data) if orm_model.extra_data else None
            )
            for orm_model in orm_models
        ]
        
    async def update_status(self, listing_id: int, status: str) -> None:
        stmt = select(ListingORM).where(ListingORM.id == listing_id)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            orm_model.status = status
            await self.session.commit()
