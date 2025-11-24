from typing import Annotated

from app.core.config import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = settings.POSTGRES_URL
engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


class Base(DeclarativeBase):
    pass
