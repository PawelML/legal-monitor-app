"""Readiness endpoint behavior."""

from __future__ import annotations

import httpx
from pytest import MonkeyPatch

from legal_monitor.config import get_settings
from legal_monitor.main import create_app


async def test_health_reports_database_readiness(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LEGAL_MONITOR_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    try:
        app = create_app()
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                response = await client.get("/health")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
