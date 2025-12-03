from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepo[T]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def add(self, obj: T) -> None:
        self.session.add(obj)

    async def remove(self, obj: T) -> None:
        self.session.delete(obj)

    async def get_by_id(self, id: UUID) -> T | None:
        obj = await self.session.execute(select(self.model).where(self.model.id == id))  # type: ignore
        return obj.scalar_one_or_none()

    async def list(self) -> list[T]:
        res = await self.session.execute(select(self.model))

        return res.scalars().all()
