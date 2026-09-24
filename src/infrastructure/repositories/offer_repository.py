from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.interfaces import OfferRepository
from src.domain.models import Offer, OfferStatus
from src.infrastructure.database.orm_models import OfferORM, OfferUrlORM


class SQLiteOfferRepository(OfferRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, offer: Offer) -> None:
        orm_model = OfferORM.from_domain(offer)
        self.session.add(orm_model)
        await self.session.commit()
        offer.id = orm_model.id

    async def add_batch(self, offers: list[Offer]) -> None:
        if not offers:
            return

        incoming_urls = [u.url for o in offers for u in o.urls]
        incoming_fingerprints = [o.fingerprint for o in offers]

        # Fetch existing URLs eager loading offer
        stmt_urls = (
            select(OfferUrlORM)
            .where(OfferUrlORM.url.in_(incoming_urls))
            .options(selectinload(OfferUrlORM.offer))
        )
        result_urls = await self.session.execute(stmt_urls)
        existing_url_orms = {u.url: u for u in result_urls.scalars().all()}

        # Fetch existing fingerprints
        stmt_fps = select(OfferORM).where(
            OfferORM.fingerprint.in_(incoming_fingerprints)
        )
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
                    self.session.add(
                        OfferUrlORM(url=url, offer_id=existing_offer_orm.id)
                    )
                else:
                    # Totally new offer
                    await self.add(offer)

            processed_urls.add(url)
            processed_fingerprints.add(offer.fingerprint)

        # Commit any leftover additions from adding new URLs
        await self.session.commit()

    async def get_by_fingerprint(self, fingerprint: str) -> Offer | None:
        stmt = select(OfferORM).where(OfferORM.fingerprint == fingerprint)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return orm_model.to_domain() if orm_model else None

    async def get_unseen_for_session(self, session_id: int) -> list[Offer]:
        stmt = select(OfferORM).where(
            OfferORM.session_id == session_id,
            OfferORM.status == OfferStatus.NEW.value,
        )
        result = await self.session.execute(stmt)
        return [orm_model.to_domain() for orm_model in result.scalars().all()]

    async def update_status(self, offer_id: int, status: str) -> None:
        stmt = update(OfferORM).where(OfferORM.id == offer_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.commit()

    async def count_for_session(self, session_id: int) -> int:
        stmt = select(func.count(OfferORM.id)).where(OfferORM.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
