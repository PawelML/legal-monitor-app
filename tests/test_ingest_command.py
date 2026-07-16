"""Command-line failure behavior."""

from __future__ import annotations

from typing import Never

from pytest import MonkeyPatch

import legal_monitor.ingest as ingest


class FakeEngine:
    """Minimal engine substitute used to avoid a real database in this test."""

    async def dispose(self) -> None:
        """Match the production engine disposal interface."""


class FailingService:
    """Service substitute that models a recorded ingestion failure."""

    def __init__(self, *_: object) -> None:
        pass

    async def import_year(self, *_: object) -> Never:
        raise RuntimeError("ELI is unavailable")


async def test_command_returns_nonzero_when_import_fails(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest, "create_engine", lambda _: FakeEngine())
    monkeypatch.setattr(ingest, "create_session_factory", lambda _: None)
    monkeypatch.setattr(ingest, "MetadataIngestionService", FailingService)

    assert await ingest.run(2026, ("DU",)) == 1
