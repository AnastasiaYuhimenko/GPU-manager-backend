from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers.v1.auth import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.client import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client

    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=0,
        decode_responses=True,
    )

    try:
        yield
    finally:
        if redis_client:
            await redis_client.close()


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
