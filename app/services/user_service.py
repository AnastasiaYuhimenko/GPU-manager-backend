from typing import Annotated
from uuid import UUID

from app.core.logger import logger
from app.db.base import SessionDep
from app.db.redis import RedisDep
from app.db.unit_of_work import UnitOfWork
from app.models.users import User
from app.schemas.users import CreateUserBody, TokenDataResponse, UserEmailId
from app.services.cookie_service import CookieService, CookieServiceDep
from app.services.jwt_service import JwtService, JwtServiceDep
from app.services.password_service import PasswordService, PasswordServiceDep
from fastapi import Depends, HTTPException, status
from redis.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(
        self,
        redis: Redis,
        jwt: JwtService,
        passwordServ: PasswordService,
        session: AsyncSession,
        cookie_service: CookieService,
    ):
        self.redis = redis
        self.jwt = jwt
        self.passwordService = passwordServ
        self.session = session
        self.cookie_service = cookie_service

    async def _login_fail(self, ip: str):
        fail_count = f"login:fail:{ip}"
        block_key = f"login:block:{ip}"
        fails = await self.redis.incr(fail_count)
        await self.redis.expire(fail_count, 900)
        if fails >= 5:
            await self.redis.set(block_key, "1", ex=900)

    async def _login_success(self, ip: str):
        fail_count = f"login:fail:{ip}"
        block_key = f"login:block:{ip}"
        await self.redis.delete(fail_count)
        await self.redis.delete(block_key)

    async def create_user(self, user_data: CreateUserBody) -> User:
        async with UnitOfWork(self.session) as uow:
            user_exists = await uow.users.is_user_exist(email=user_data.email)
            if user_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"email": "Пользователь с таким email уже существует"},
                )
            user = User(
                email=user_data.email,
                password=self.passwordService.get_password_hash(user_data.password),
                name=user_data.name,
                lastname=user_data.lastname,
            )
            await uow.users.add(user)
        return user_data

    async def get_user_by_email(self, email: str):
        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user_by_email(email)
            return row

    async def get_user_by_id(self, id: UUID):
        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user_by_id(id)
            return row

    async def _check_ip(self, ip: str, email: str):
        block_key = f"login:block:{ip}"
        blocked_ttl = await self.redis.ttl(block_key)
        if blocked_ttl > 0:
            minutes = blocked_ttl // 60
            logger.info(f"Неудачная попытка входа: EMAIL: {email}, IP: {ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Слишком много попыток. Попробуй через {minutes} минут"
            )

    async def login_user(self, email: str, password: str):
        ip = self.cookie_service.request.client.host
        await self._check_ip(ip=ip, email=email)
        async with UnitOfWork(self.session) as uow:
            row = await uow.users.get_user_by_email(email=email)
            if row is None:
                await self._login_fail(ip=ip)
                logger.info(f"Неудачная попытка входа: EMAIL: {email}, IP: {ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"email": "Неверный email или пароль", "password": "Неверный email или пароль"},
                )
        password_correct = row.password

        if not self.passwordService.verify_password(plain_password=password, hashed_password=password_correct):
            await self._login_fail(ip=ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"email": "Неверный email или пароль", "password": "Неверный email или пароль"},
            )
        data = UserEmailId(id=str(row.id), email=row.email).model_dump()
        access_token = self.jwt.create_access_token(data=data)
        refresh_token = self.jwt.create_refresh_token(data=data)

        await self.cookie_service.set_cookie(name="access_token", value=access_token)
        await self.cookie_service.set_cookie(name="refresh_token", value=refresh_token)
        await self._login_success(ip=ip)
        return TokenDataResponse(user_id=row.id, email=row.email, token_type="bearer")

    async def logout(self):
        await self.cookie_service.delete_cookie(name="access_token")
        await self.cookie_service.delete_cookie(name="refresh_token")


def get_user_service(
    redis: RedisDep,
    jwt: JwtServiceDep,
    passwordServ: PasswordServiceDep,
    session: SessionDep,
    cookie_service: CookieServiceDep,
) -> UserService:
    return UserService(redis=redis, jwt=jwt, passwordServ=passwordServ, session=session, cookie_service=cookie_service)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
