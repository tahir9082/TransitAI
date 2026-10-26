import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Fetch the URL from Docker environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/transit_db")

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base class for your database tables
Base = declarative_base()

# Dependency to yield database sessions to FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()