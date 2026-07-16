"""Contract tests for the documented ELI yearly-list response."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from legal_monitor.eli.client import ELIClient


async def test_client_parses_yearly_list_fixture() -> None:
    payload_path = Path(__file__).parent / "fixtures" / "eli_acts_du_2026.json"
    payload = json.loads(payload_path.read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/eli/acts/DU/2026"
        assert request.headers["accept"] == "application/json"
        return httpx.Response(200, json=payload)

    client = ELIClient(
        "https://api.sejm.gov.pl/eli", transport=httpx.MockTransport(handler)
    )

    records = await client.list_acts("DU", 2026)

    assert len(records) == 1
    assert records[0].eli == "DU/2026/946"
    assert records[0].change_date is not None
    assert records[0].change_date.tzinfo is not None
    assert records[0].raw_metadata["ELI"] == "DU/2026/946"


async def test_client_rejects_incomplete_payload() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": 1, "items": [{"ELI": "DU/2026/1"}]})

    client = ELIClient(
        "https://api.sejm.gov.pl/eli", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(ValueError):
        await client.list_acts("DU", 2026)
