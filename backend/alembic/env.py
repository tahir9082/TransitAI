import asyncio
from logging.config import fileConfig
import os

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Import your Base and Models so Alembic can see them
from app.core.database import Base
from app.models import UserProfile

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Tell Alembic to use your Base metadata for autogeneration
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:mysecretpassword@db:5432/transit_db")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    # This is where target_metadata is passed to the migration context
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    ini_section = config.get_section(config.config_ini_section, {})
    ini_section["sqlalchemy.url"] = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:mysecretpassword@db:5432/transit_db"
    )

    connectable = async_engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()