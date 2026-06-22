from src.domain.interfaces import OfferRepository
from src.domain.models import Offer, OfferStatus, OfferUrl
from src.infrastructure.database.orm_models import OfferORM, OfferUrlORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json

class SQLiteOfferRepository(OfferRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, offer: Offer) -> None:
        extra_data_json = json.dumps(offer.extra_data) if offer.extra_data else None
        
        # Create URLs
        url_orms = [
            OfferUrlORM(url=u.url, source=u.source) for u in offer.urls
        ]

        orm_model = OfferORM(
            fingerprint=offer.fingerprint,
            title=offer.title,
            status=offer.status.value,
            session_id=offer.session_id,
            price=offer.price,
            location=offer.location,
            description=offer.description,
            extra_data=extra_data_json,
            urls=url_orms
        )
        self.session.add(orm_model)
        await self.session.commit()
        offer.id = orm_model.id

    async def add_batch(self, offers: List[Offer]) -> None:
        if not offers:
            return
            
        # SQLite doesn't natively support easy bulk insert with nested relationships and ON CONFLICT
        # in a single statement without complex CTEs, so for batch adding we will iterate and add,
        # or we could use the ORM directly. Since the batch might contain conflicts, we handle them carefully.
        
        for offer in offers:
            # Check if exists
            existing = await self.get_by_fingerprint(offer.fingerprint)
            if not existing:
                await self.add(offer)
        
    async def get_by_fingerprint(self, fingerprint: str) -> Optional[Offer]:
        stmt = select(OfferORM).where(OfferORM.fingerprint == fingerprint)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            extra_data = json.loads(orm_model.extra_data) if orm_model.extra_data else None
            return Offer(
                id=orm_model.id,
                fingerprint=orm_model.fingerprint,
                title=orm_model.title,
                status=OfferStatus(orm_model.status),
                session_id=orm_model.session_id,
                price=orm_model.price,
                location=orm_model.location,
                description=orm_model.description,
                extra_data=extra_data,
                urls=[OfferUrl(url=u.url, source=u.source) for u in orm_model.urls]
            )
        return None

    async def get_unseen_for_session(self, session_id: int) -> List[Offer]:
        stmt = select(OfferORM).where(
            OfferORM.session_id == session_id,
            OfferORM.status == OfferStatus.NEW.value
        )
        result = await self.session.execute(stmt)
        orm_models = result.scalars().all()
        
        return [
            Offer(
                id=orm_model.id,
                fingerprint=orm_model.fingerprint,
                title=orm_model.title,
                status=OfferStatus(orm_model.status),
                session_id=orm_model.session_id,
                price=orm_model.price,
                location=orm_model.location,
                description=orm_model.description,
                extra_data=json.loads(orm_model.extra_data) if orm_model.extra_data else None,
                urls=[OfferUrl(url=u.url, source=u.source) for u in orm_model.urls]
            )
            for orm_model in orm_models
        ]
        
    async def update_status(self, offer_id: int, status: str) -> None:
        stmt = select(OfferORM).where(OfferORM.id == offer_id)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            orm_model.status = status
            await self.session.commit()
