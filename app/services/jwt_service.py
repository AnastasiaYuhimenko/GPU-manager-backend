from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from app.core.config import settings
from app.db.redis import RedisDep
from app.schemas.users import TokenDataResponse, UserEmailId
from app.services.cookie_service import CookieService, CookieServiceDep
from fastapi import Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from redis.asyncio import Redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class JwtService:
    def __init__(self, response: Response, request: Request, cookie_service: CookieService, redis: Redis) -> None:
        self.secure = settings.SECURE
        self.cookie_service = cookie_service
        self.redis = redis

    async def token_block(self, token: str):
        block_cookie = f"token:block:{token}"
        time_last = await self.get_token_life_time(token=token)
        seconds_left = int(time_last.total_seconds())
        if seconds_left <= 0:
            seconds_left = 1

        await self.redis.set(block_cookie, "1", ex=seconds_left)

    async def _is_token_blocked(self, token: str):
        block_key = f"token:block:{token}"
        blocked_ttl = self.redis.ttl(block_key)
        return not await blocked_ttl > 0

    def _create_token(self, to_encode: dict, expire: datetime, token_type: str):
        to_encode.update({"exp": expire.timestamp(), "token_type": token_type})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        return self._create_token(to_encode=to_encode, expire=expire, token_type="access_token")

    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return self._create_token(to_encode=to_encode, expire=expire, token_type="refresh_token")

    async def verify_token(self, token: str, refresh_token: str) -> TokenDataResponse:
        if not await self._is_token_blocked(token=token):
            raise credentials_exception
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("id")
            if user_id is None:
                raise credentials_exception
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            try:
                payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("id")
                if user_id is None:
                    raise credentials_exception
                data = UserEmailId(id=payload.get("id"), email=payload.get("email")).model_dump()

                new_access_token = self.create_access_token(data=data)
                new_refresh_token = self.create_refresh_token(data=data)
                await self.cookie_service.set_cookie(
                    name="access_token", value=new_access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                )
                await self.cookie_service.set_cookie(
                    name="refresh_token",
                    value=new_refresh_token,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                )
                return TokenDataResponse(
                    user_id=user_id,
                    email="",
                    token_type=payload.get("token_type"),
                )
            except jwt.InvalidTokenError:
                raise credentials_exception from None

        return TokenDataResponse(user_id=user_id, email=payload.get("email"), token_type=payload.get("token_type"))

    async def get_current_user(self):
        token = await self.cookie_service.get_cookie("access_token")
        refresh_token = await self.cookie_service.get_cookie("refresh_token")

        if not token and not refresh_token:
            raise credentials_exception

        user = await self.verify_token(
            token=token,
            refresh_token=refresh_token,
        )
        return user

    async def get_token_life_time(self, token: str):
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_exp_get = payload.get("exp")
        token_exp = datetime.fromtimestamp(token_exp_get, tz=UTC)
        return token_exp - datetime.now(UTC)


def get_jwt_service(response: Response, request: Request, cookie_service: CookieServiceDep, redis: RedisDep):
    return JwtService(response=response, request=request, cookie_service=cookie_service, redis=redis)


JwtServiceDep = Annotated[JwtService, Depends(get_jwt_service)]
