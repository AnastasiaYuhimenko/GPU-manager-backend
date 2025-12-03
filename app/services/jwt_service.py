from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from app.core.config import settings
from app.db.base import get_session
from app.db.unit_of_work import UnitOfWork
from app.models.users import User
from app.schemas.users import TokenDataResponse, UserSchemeWithIdResponse
from fastapi import Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class jwtService:
    def __init__(self, response: Response, request: Request, session: AsyncSession) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.response = response
        self.request = request
        self.session = session
        self.UserDep = Annotated[User, Depends(self.get_current_user)]
        self.secure = settings.SECURE
        self.UserDep = Annotated[User, Depends(self.get_current_user)]

    def verify_password(self, plain_password: str, hashed_password: str):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return pwd_context.hash(password)

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
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("id")
            email = payload.get("email")
            if user_id is None:
                raise credentials_exception
            token_data = TokenDataResponse(user_id=user_id, email=email, token_type=payload.get("token_type"))
        except jwt.InvalidTokenError, jwt.ExpiredSignatureError:
            try:
                payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("email")
                if user_id is None:
                    raise credentials_exception
                token_data = TokenDataResponse(user_id=user_id, email="", token_type=payload.get("token_type"))

                new_access_token = self.create_access_token(data={"sub": user_id})
                new_refresh_token = self.create_refresh_token(data={"sub": user_id})
                self.response.set_cookie(
                    key="access_token",
                    value=new_access_token,
                    httponly=True,
                    secure=self.secure,
                    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )
                self.response.set_cookie(
                    key="refresh_token",
                    value=new_refresh_token,
                    httponly=True,
                    secure=self.secure,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                )
                return TokenDataResponse(
                    user_id=user_id,
                    email="",
                    token_type=payload.get("token_type"),
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                )
            except jwt.InvalidTokenError:
                raise credentials_exception

        async with UnitOfWork(self.session) as uow:
            user = await uow.users.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        user = UserSchemeWithIdResponse(
            id=str(user.id),
            email=str(user.email),
            name=str(user.name),
            lastname=str(user.lastname),
        )

        return TokenDataResponse(user_id=user_id, email=user.email, token_type=payload.get("token_type"))

    async def get_current_user(self):
        token = self.request.cookies.get("access_token")
        refresh_token = self.request.cookies.get("refresh_token")

        if not token and not refresh_token:
            raise credentials_exception

        user = await self.verify_token(
            token=token,
            refresh_token=refresh_token,
        )
        return user


def get_jwt_service(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    return jwtService(response=response, request=request, session=session)


JwtServiceDep = Annotated[jwtService, Depends(get_jwt_service)]
