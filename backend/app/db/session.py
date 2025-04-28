from fastapi import Request
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL_ASYNC, future=True, echo=False)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)



def get_db(
    request: Request
):
    """
    Dependency function that yields db sessions
    """
    yield request.state.db.session
