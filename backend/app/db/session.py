from sqlalchemy.orm import declarative_base
from app.config import settings

Base = declarative_base()

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(
        settings.get_database_url(),
        echo=False,
        future=True,
        pool_pre_ping=True
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
except Exception as e:
    print(f"Database engine init notice: {e}. Operating in standalone mode.")
    engine = None
    AsyncSessionLocal = None

async def get_db():
    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        yield None

async def clear_database():
    """
    Clears all rows from the database tables: summaries, captions, events, alerts, cameras.
    """
    if engine is not None:
        from sqlalchemy import text
        try:
            async with engine.begin() as conn:
                for table in ["alerts", "events", "captions", "summaries", "cameras"]:
                    try:
                        await conn.execute(text(f"DELETE FROM {table};"))
                    except Exception as err:
                        print(f"Notice: clearing table {table} skipped or table not created ({err})")
            return True
        except Exception as e:
            print(f"Notice: clear_database error: {e}")
            return False
    return True

