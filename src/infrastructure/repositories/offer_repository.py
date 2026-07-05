from src.domain.interfaces import OfferRepository
from src.domain.models import Offer, OfferStatus, OfferUrl, OfferPrice, OfferCategory
from src.infrastructure.database.orm_models import OfferORM, OfferUrlORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import json

class SQLiteOfferRepository(OfferRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, offer: Offer) -> None:
        extra_data_json = json.dumps(offer.extra_data) if offer.extra_data else None
        
        # Create URLs
        url_orms = [
            OfferUrlORM(url=u.url) for u in offer.urls
        ]

        price_min = offer.price.price_min if offer.price else None
        price_max = offer.price.price_max if offer.price else None
        currency = offer.price.currency if offer.price else None
        period = offer.price.period if offer.price else None
        special_status = offer.price.special_status if offer.price else None
        is_free = offer.price.is_free if offer.price else False
        is_negotiable = offer.price.is_negotiable if offer.price else False

        category_str = offer.category.value if offer.category else None

        orm_model = OfferORM(
            fingerprint=offer.fingerprint,
            title=offer.title,
            status=offer.status.value,
            session_id=offer.session_id,
            price_min=price_min,
            price_max=price_max,
            currency=currency,
            period=period,
            special_status=special_status,
            is_free=is_free,
            is_negotiable=is_negotiable,
            category=category_str,
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
            
        incoming_urls = [u.url for o in offers for u in o.urls]
        incoming_fingerprints = [o.fingerprint for o in offers]

        # Fetch existing URLs eager loading offer
        stmt_urls = select(OfferUrlORM).where(OfferUrlORM.url.in_(incoming_urls)).options(selectinload(OfferUrlORM.offer))
        result_urls = await self.session.execute(stmt_urls)
        existing_url_orms = {u.url: u for u in result_urls.scalars().all()}

        # Fetch existing fingerprints
        stmt_fps = select(OfferORM).where(OfferORM.fingerprint.in_(incoming_fingerprints))
        result_fps = await self.session.execute(stmt_fps)
        existing_offer_orms = {o.fingerprint: o for o in result_fps.scalars().all()}

        processed_fingerprints = set()
        processed_urls = set()

        for offer in offers:
            if not offer.urls:
                continue
            
            url = offer.urls[0].url

            if url in processed_urls:
                continue
            
            existing_url_orm = existing_url_orms.get(url)
            
            if existing_url_orm:
                if existing_url_orm.offer.fingerprint != offer.fingerprint:
                    # Conflict D-01: Same URL, different fingerprint -> Delete old, insert new
                    await self.session.delete(existing_url_orm.offer)
                    await self.session.flush()
                    await self.add(offer)
                else:
                    # Same URL and same fingerprint -> exact duplicate, skip
                    pass
            else:
                # URL doesn't exist. Check fingerprint.
                if offer.fingerprint in processed_fingerprints:
                    continue

                existing_offer_orm = existing_offer_orms.get(offer.fingerprint)
                if existing_offer_orm:
                    # Fingerprint exists but URL doesn't -> add new URL to existing offer
                    self.session.add(OfferUrlORM(url=url, offer_id=existing_offer_orm.id))
                else:
                    # Totally new offer
                    await self.add(offer)
            
            processed_urls.add(url)
            processed_fingerprints.add(offer.fingerprint)
            
        # Commit any leftover additions from adding new URLs
        await self.session.commit()

    def _map_orm_to_domain(self, orm_model: OfferORM) -> Offer:
        extra_data = json.loads(orm_model.extra_data) if orm_model.extra_data else None
        
        has_price = any([
            orm_model.price_min is not None, 
            orm_model.price_max is not None, 
            orm_model.currency is not None, 
            orm_model.period is not None, 
            orm_model.special_status is not None,
            orm_model.is_free,
            orm_model.is_negotiable
        ])
        
        offer_price = None
        if has_price:
            offer_price = OfferPrice(
                price_min=orm_model.price_min,
                price_max=orm_model.price_max,
                currency=orm_model.currency,
                period=orm_model.period,
                special_status=orm_model.special_status,
                is_free=orm_model.is_free,
                is_negotiable=orm_model.is_negotiable
            )
            
        offer_category = OfferCategory(orm_model.category) if orm_model.category else None
            
        return Offer(
            id=orm_model.id,
            fingerprint=orm_model.fingerprint,
            title=orm_model.title,
            status=OfferStatus(orm_model.status),
            session_id=orm_model.session_id,
            price=offer_price,
            location=orm_model.location,
            description=orm_model.description,
            extra_data=extra_data,
            urls=[OfferUrl(url=u.url) for u in orm_model.urls],
            category=offer_category
        )

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[Offer]:
        stmt = select(OfferORM).where(OfferORM.fingerprint == fingerprint).options(selectinload(OfferORM.urls))
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            return self._map_orm_to_domain(orm_model)
        return None

    async def get_unseen_for_session(self, session_id: int) -> List[Offer]:
        stmt = select(OfferORM).where(
            OfferORM.session_id == session_id,
            OfferORM.status == OfferStatus.NEW.value
        ).options(selectinload(OfferORM.urls))
        result = await self.session.execute(stmt)
        orm_models = result.scalars().all()
        
        return [self._map_orm_to_domain(orm_model) for orm_model in orm_models]
        
    async def update_status(self, offer_id: int, status: str) -> None:
        stmt = select(OfferORM).where(OfferORM.id == offer_id)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            orm_model.status = status
            await self.session.commit()

    async def count_for_session(self, session_id: int) -> int:
        from sqlalchemy import func
        stmt = select(func.count(OfferORM.id)).where(OfferORM.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
