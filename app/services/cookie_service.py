from typing import Annotated

from app.core.config import settings
from fastapi import Depends, Request, Response


class CookieService:
    def __init__(self, request: Request, response: Response) -> None:
        self.request = request
        self.response = response

    async def set_cookie(self, name: str, value: str, max_age: int | None = None) -> None:
        self.response.set_cookie(
            key=name,
            value=value,
            httponly=True,
            secure=settings.SECURE,
            max_age=max_age,
        )

    async def get_cookie(self, name: str) -> str:
        return self.request.cookies.get(name)

    async def delete_cookie(self, name: str) -> str:
        self.response.delete_cookie(key=name)


def get_cookie_service(request: Request, response: Response) -> CookieService:
    return CookieService(request=request, response=response)


CookieServiceDep = Annotated[CookieService, Depends(get_cookie_service)]
