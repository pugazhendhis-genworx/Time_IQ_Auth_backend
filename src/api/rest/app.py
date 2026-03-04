from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.data.models.postgres  # noqa: F401
from src.api.rest.routes.Auth_routes import auth_router
from src.api.rest.routes.health_router import health_router
from src.data.clients.postgres_client import Base, async_session_maker, engine
from src.utils.role_seed import seed_roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        await seed_roles(session)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="TimeIQ_AUTH", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(health_router)
    return app
