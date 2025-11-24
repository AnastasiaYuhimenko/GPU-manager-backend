# from app.auth.schemas import UserCreate, UserOut
# from app.auth.utils import (
#     get_password_hash,
# )
from app.schemas.users import TokenData, UserCreate, UserLogin, UserOut
from app.services.user_service import UserServiceDep
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate, user_service: UserServiceDep):
    return await user_service.create_user(user)


@router.post("/login", response_model=TokenData, status_code=200)
async def login(user: UserLogin, user_service: UserServiceDep, responce: Response, request: Request):
    return await user_service.login_user(email=user.email, password=user.password, response=responce, request=request)


# @router.post("/logout")


# @router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
# async def login(
#     user_repository: UserRepositoryDep,
#     user: UserLogin,
#     response: Response,
# ):
#     user_obj = await user_repository.get_user(user.login)
#     if user_obj is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"login": "Пользователь с таким логином не найден"},
#         )
#     if not verify_password(user.password, str(user_obj.password)):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"password": "Неверный пароль"},
#         )
#     data = {"sub": str(user_obj.id)}

#     access_token = create_access_token(data=data)
#     refresh_token = create_refresh_token(data=data)

#     response.set_cookie("access_token", path="/", value=access_token, httponly=True)
#     response.set_cookie("refresh_token", path="/", value=refresh_token, httponly=True)

#     return Token(access_token=access_token, refresh_token=refresh_token)


# @router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
# async def logout_user(response: Response):
#     response.delete_cookie(key="access_token", path="/")
#     response.delete_cookie(key="refresh_token", path="/")
#     return {"message": "Вы успешно вышли из системы"}


# @router.post("/refresh", status_code=status.HTTP_200_OK, response_model=Token)
# async def refresh_token(request: Request, session: SessionDep, response: Response):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     refresh_token = request.cookies.get("refresh_token")
#     if refresh_token is None:
#         raise credentials_exception
#     token_data = await verify_token(token=refresh_token, session=session)
#     if token_data.token_type != "refresh_token":
#         raise credentials_exception

#     data = {"sub": str(token_data.user_id)}

#     access_token = create_access_token(data=data)

#     response.set_cookie("access_token", path="/", value=access_token, httponly=True)

#     return Token(access_token=access_token, refresh_token=refresh_token)
