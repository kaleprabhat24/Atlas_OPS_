import asyncio
import os
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

async def check_postgres():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        print("✅ PostgreSQL: Connected successfully.")
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed. Ensure Postgres is running on localhost:5432. Error: {str(e)}")

async def check_redis():
    try:
        import redis.asyncio as aioredis
        pool = aioredis.from_url(settings.redis_url)
        await pool.ping()
        await pool.aclose()
        print("✅ Redis: Connected successfully.")
    except Exception as e:
        print(f"❌ Redis: Connection failed. Ensure Redis is running on localhost:6379. Error: {str(e)}")

def check_models():
    models = [
        settings.fraud_model_path,
        settings.failure_model_path,
        settings.routing_model_path
    ]
    for path in models:
        if Path(path).exists():
            print(f"✅ ML Model: Found {path}")
        else:
            print(f"⚠️ ML Model: Missing {path} (Fallback models will be used)")

async def main():
    print("--- ATLAS-OPS Local Setup Check ---")
    await check_postgres()
    await check_redis()
    check_models()
    print("-----------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
