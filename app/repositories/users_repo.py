from uuid import UUID

from app.models.users import User
from app.repositories.base_repo import BaseRepo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepo[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, model=User)

    async def add(self, user: User) -> User:
        self.session.add(user)
        return user

    async def get_user(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()
