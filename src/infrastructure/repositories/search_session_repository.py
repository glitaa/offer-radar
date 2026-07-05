from src.domain.interfaces import SearchSessionRepository
from src.domain.models import SearchSession
from src.infrastructure.database.orm_models import SearchSessionORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

class SQLiteSearchSessionRepository(SearchSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, session_obj: SearchSession) -> None:
        orm_model = SearchSessionORM(
            search_url=session_obj.search_url
        )
        self.session.add(orm_model)
        await self.session.commit()
        session_obj.id = orm_model.id
        
    async def get_by_url(self, url: str) -> Optional[SearchSession]:
        stmt = select(SearchSessionORM).where(SearchSessionORM.search_url == url)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            return SearchSession(
                id=orm_model.id,
                search_url=orm_model.search_url
            )
        return None

    async def get_all(self) -> list[SearchSession]:
        stmt = select(SearchSessionORM)
        result = await self.session.execute(stmt)
        orm_models = result.scalars().all()
        return [
            SearchSession(id=model.id, search_url=model.search_url)
            for model in orm_models
        ]

    async def delete(self, session_id: int) -> None:
        stmt = select(SearchSessionORM).where(SearchSessionORM.id == session_id)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        
        if orm_model:
            await self.session.delete(orm_model)
            await self.session.commit()
