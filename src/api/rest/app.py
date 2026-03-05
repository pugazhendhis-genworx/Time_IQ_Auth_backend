from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import src.data.models.postgres  # noqa: F401
from src.api.rest.routes.Auth_routes import auth_router
from src.api.rest.routes.health_router import health_router
from src.api.rest.routes.user_routes import user_router
from src.data.clients.postgres_client import Base, async_session_maker, engine
from src.utils.role_seed import seed_roles

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


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
        allow_origins=["http://localhost:3000","http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(user_router)

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard():
        html = (STATIC_DIR / "admin.html").read_text(encoding="utf-8")
        return HTMLResponse(content=html)

    return app
