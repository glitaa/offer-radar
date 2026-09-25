from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces import SearchSessionRepository
from src.domain.models import SearchSession
from src.infrastructure.database.orm_models import SearchSessionORM


class SQLiteSearchSessionRepository(SearchSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, session_obj: SearchSession) -> None:
        orm_model = SearchSessionORM.from_domain(session_obj)
        self.session.add(orm_model)
        await self.session.commit()
        session_obj.id = orm_model.id

    async def get_by_url(self, url: str) -> SearchSession | None:
        stmt = select(SearchSessionORM).where(SearchSessionORM.search_url == url)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return orm_model.to_domain() if orm_model else None

    async def get_by_query(self, query: str) -> SearchSession | None:
        stmt = select(SearchSessionORM).where(SearchSessionORM.query == query)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return orm_model.to_domain() if orm_model else None

    async def get_all(self) -> list[SearchSession]:
        stmt = select(SearchSessionORM)
        result = await self.session.execute(stmt)
        return [model.to_domain() for model in result.scalars().all()]

    async def delete(self, session_id: int) -> None:
        orm_model = await self.session.get(SearchSessionORM, session_id)
        if orm_model:
            await self.session.delete(orm_model)
            await self.session.commit()
