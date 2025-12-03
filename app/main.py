from contextlib import asynccontextmanager

from app.db.redis import connect_to_redis, disconnect_from_redis
from app.routers.v1.auth import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_redis()
    yield
    await disconnect_from_redis()


app = FastAPI(
    lifespan=lifespan,
    title="GPU-Manager",
    description="Менеджер по распределению GPU",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redocs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth_router)
