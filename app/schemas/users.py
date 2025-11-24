import re
from typing import Annotated

from fastapi import HTTPException, status
from pydantic import AfterValidator, BaseModel, EmailStr


def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password": "Пароль должен содержать как минимум 8 символов"},
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password": "пароль должен содержать хотябы одну заглавную букву"},
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password": "Пароль должен содеражть хотябы одну строчную букву"},
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"password": "Пароль должен содержать хотябы одну цифру"}
        )
    if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:,.<>/?\\|`~]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password": "Пароль должен содержать хотябы один специальный символ"},
        )

    return password


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    lastname: str
    password: Annotated[str, AfterValidator(validate_password)]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    email: EmailStr
    name: str
    lastname: str


class UserAllData(BaseModel):
    id: str
    email: EmailStr
    name: str
    lastname: str
    password: str


class UserSchemeWithId(UserOut):
    id: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    email: EmailStr
    token_type: str | None


class MessageResponse(BaseModel):
    message: str
