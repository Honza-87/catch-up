"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from catchup.config import get_settings
from catchup.errors import AppError
from catchup.logging_config import configure_logging


def _register_routers(app: FastAPI) -> None:
    """Attach feature routers. Imported lazily so the factory stays cohesive."""
    from catchup.api import auth, members, places

    app.include_router(auth.router)
    app.include_router(members.router)
    app.include_router(places.router)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="catch-up", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_base_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    _register_routers(app)
    return app


app = create_app()


def main() -> None:
    """Entry point for `catchup-api` / local `python -m catchup.app`."""
    import uvicorn

    uvicorn.run("catchup.app:app", host="0.0.0.0", port=8000)
