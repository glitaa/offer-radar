import asyncio
import os
from src.infrastructure.database.config import engine
from src.infrastructure.database.orm_models import Base

async def init_db():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("Database schema created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
