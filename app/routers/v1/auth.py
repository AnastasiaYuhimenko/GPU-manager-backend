from app.schemas.users import CreateUserBody, LoginUserBody, TokenDataResponse
from app.services.jwt_service import JwtServiceDep
from app.services.user_service import UserServiceDep
from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenDataResponse, status_code=status.HTTP_201_CREATED)
async def register(user: CreateUserBody, user_service: UserServiceDep):
    user_data = await user_service.create_user(user)
    return await user_service.login_user(email=user_data.email, password=user_data.password)


@router.post("/login", response_model=TokenDataResponse, status_code=status.HTTP_200_OK)
async def login(user: LoginUserBody, user_service: UserServiceDep):
    return await user_service.login_user(email=user.email, password=user.password)


@router.get("/me")
async def get_me(jwt_serv: JwtServiceDep):
    return await jwt_serv.get_current_user()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
