"""
Async SQLAlchemy engine + session factory for ATLAS-OPS.
Connects to LOCAL PostgreSQL (managed via pgAdmin).
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_all_tables() -> None:
    """Create all SQLModel tables on startup."""
    # Import all models to register their metadata
    import app.models.transaction  # noqa: F401
    import app.models.gateway  # noqa: F401
    import app.models.ml_result  # noqa: F401

    from sqlalchemy.exc import SQLAlchemyError
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("database_tables_created")
    except SQLAlchemyError as exc:
        logger.error(
            "database_connection_failed",
            error=str(exc),
            hint="Ensure PostgreSQL is running in pgAdmin and 'atlas_ops' database exists. "
                 "Run: python setup_db.py",
        )
        print("\n" + "=" * 60)
        print("❌ DATABASE CONNECTION FAILED")
        print("=" * 60)
        print(f"Error: {exc}")
        print()
        print("Quick fix steps:")
        print("  1. Open pgAdmin and ensure PostgreSQL server is running")
        print("  2. Run: python setup_db.py")
        print("  3. Check .env file — update DATABASE_URL with your credentials:")
        print(f"     Current: {settings.database_url}")
        print("=" * 60 + "\n")
        import sys
        sys.exit(1)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
