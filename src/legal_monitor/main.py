"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and dispose of database resources with the application."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    app.state.database_engine = engine
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    """Build the HTTP application without opening a database connection yet."""
    app = FastAPI(title="PrawoRadar", version="0.0.0", lifespan=lifespan)

    @app.get("/health")
    async def health(request: Request) -> dict[str, str]:
        """Report readiness only after a minimal database round trip."""
        try:
            async with request.app.state.session_factory() as session:
                await session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            ) from exc
        return {"status": "ok"}

    return app


app = create_app()
