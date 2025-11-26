from typing import Annotated
from uuid import UUID

from app.core.logger import logger
from app.db.base import get_session
from app.db.redis_con import redis_dep
from app.db.unit_of_work import UnitOfWork
from app.models.users import User
from app.schemas.users import TokenData, UserAllData, UserCreate
from app.security.jwt_service import create_access_token, create_refresh_token, get_password_hash, verify_password
from fastapi import Depends, HTTPException, Request, Response, status
from redis.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.redis = redis

    async def _login_fail(self, ip: str):
        fail_count = f"login:fail:{ip}"
        block_key = f"login:block:{ip}"
        fails = await self.redis.incr(fail_count)
        await self.redis.expire(fail_count, 900)
        if fails >= 5:
            await self.redis.set(block_key, "1", ex=900)

    async def create_user(self, user_data: UserCreate, request: Request, response: Response) -> User:
        user_exists = await self.get_user(user_data.email)
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"email": "Пользователь с таким email уже существует"},
            )
        user = User(
            email=user_data.email,
            password=get_password_hash(user_data.password),
            name=user_data.name,
            lastname=user_data.lastname,
        )
        async with UnitOfWork(self.session) as uow:
            await uow.users.add(user)
        return await self.login_user(
            email=user_data.email, password=user_data.password, request=request, response=response
        )

    async def get_user(self, email: str):
        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user(email)
            return row

    async def get_user_by_id(self, id: UUID):
        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user_by_id(id)
            return row

    async def login_user(self, email: str, password: str, response: Response, request: Request):
        ip = request.client.host
        block_key = f"login:block:{ip}"
        blocked_ttl = await self.redis.ttl(block_key)
        if blocked_ttl > 0:
            minutes = blocked_ttl // 60
            logger.info(f"Неудачная попытка входа: EMAIL: {email}, IP: {ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Слишком много попыток. Попробуй через {minutes} минут"
            )

        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user(email=email)
            if row is None:
                await self._login_fail(ip=ip)
                logger.info(f"Неудачная попытка входа: EMAIL: {email}, IP: {ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail={"email": "Неверный email или пароль"}
                )
        password_correct = row.password

        if not verify_password(plain_password=password, hashed_password=password_correct):
            await self._login_fail(ip=ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"password": "Неверный email или пароль"}
            )

        access_token = create_access_token(
            data=UserAllData(
                id=str(row.id), email=row.email, name=row.name, lastname=row.lastname, password=password
            ).model_dump()
        )
        refresh_token = create_refresh_token(
            data=UserAllData(
                id=str(row.id), email=row.email, name=row.name, lastname=row.lastname, password=password
            ).model_dump()
        )

        response.set_cookie("access_token", path="/", value=access_token, httponly=True)
        response.set_cookie("refresh_token", path="/", value=refresh_token, httponly=True)

        return TokenData(user_id=row.id, email=row.email, token_type="bearer")

    async def logout(response: Response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")


def get_user_service(session: AsyncSession = Depends(get_session), redis: Redis = Depends(redis_dep)) -> UserService:
    return UserService(session, redis=redis)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
