from datetime import UTC, datetime, timedelta

import jwt
from app.core.config import settings
from app.db.unit_of_work import UnitOfWork
from app.schemas.users import TokenData, UserSchemeWithId
from fastapi import HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_token(to_encode: dict, expire: datetime, token_type: str):
    to_encode.update({"exp": expire.timestamp(), "token_type": token_type})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return create_token(to_encode=to_encode, expire=expire, token_type="access_token")


def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(days=15)
    return create_token(to_encode=to_encode, expire=expire, token_type="refresh_token")


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def verify_token(token: str, refresh_token: str, response: Response, session: AsyncSession) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        userid = payload.get("sub")
        if userid is None:
            raise credentials_exception
        token_data = TokenData(user_id=userid, email="", token_type=payload.get("token_type"))
    except jwt.InvalidTokenError:
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            userid = payload.get("sub")
            if userid is None:
                raise credentials_exception
            token_data = TokenData(user_id=userid, email="", token_type=payload.get("token_type"))

            new_access_token = create_access_token(data={"sub": userid})
            new_refresh_token = create_refresh_token(data={"sub": userid})
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=True,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
            response.set_cookie(
                key="refresh_token", value=new_refresh_token, httponly=True, secure=True, max_age=15 * 24 * 60 * 60
            )
            return TokenData(
                user_id=userid,
                email="",
                token_type=payload.get("token_type"),
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            )
        except jwt.InvalidTokenError:
            raise credentials_exception

    async with UnitOfWork(session) as uow:
        user = await uow.users.get_user_by_id(userid)
    if user is None:
        raise credentials_exception
    user = UserSchemeWithId(
        id=str(user.id),
        email=str(user.email),
        name=str(user.name),
        surname=str(user.surname),
        lastname=str(user.lastname),
    )

    return TokenData(user_id=userid, email=user.email, token_type=payload.get("token_type"))


async def get_current_user(
    request: Request,
):
    token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token and not refresh_token:
        raise credentials_exception

    user = await verify_token(token=token, refresh_token=refresh_token)  # type: ignore
    return user
