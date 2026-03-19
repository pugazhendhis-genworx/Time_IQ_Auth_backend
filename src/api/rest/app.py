from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import src.data.models.postgres  # noqa: F401
from src.api.rest.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
)
from src.api.rest.middleware.request_context import RequestContextMiddleware
from src.api.rest.routes.Auth_routes import auth_router
from src.api.rest.routes.health_router import health_router
from src.api.rest.routes.user_routes import user_router
from src.config.settings import settings
from src.observability.logging.logging import set_up_logger

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

set_up_logger()


def create_app() -> FastAPI:
    app = FastAPI(title="TimeIQ_AUTH")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, settings.BACKEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(user_router)

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard():
        html = (STATIC_DIR / "admin.html").read_text(encoding="utf-8")
        return HTMLResponse(content=html)

    return app
