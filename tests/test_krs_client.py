"""Contract tests for the minimal public KRS current-extract adapter."""

from __future__ import annotations

import httpx
import pytest

from legal_monitor.krs.client import KrsClient, KrsNotFoundError, KrsSourceError


def current_extract_payload() -> dict[str, object]:
    """Return the minimal official-KRS-shaped fixture used by this adapter."""
    return {
        "odpis": {
            "naglowekA": {"numerKRS": "0000500605", "stanZDnia": "27.06.2026"},
            "dane": {
                "dzial1": {
                    "danePodmiotu": {
                        "nazwa": "Example sp. z o.o.",
                        "formaPrawna": "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
                        "identyfikatory": {"nip": "5272710534"},
                    }
                },
                "dzial3": {
                    "przedmiotDzialalnosci": {
                        "przedmiotPrzewazajacejDzialalnosci": [
                            {"kodDzial": "61", "kodKlasa": "10", "kodPodklasa": "Z"}
                        ],
                        "przedmiotPozostalejDzialalnosci": [
                            {"kodDzial": "43", "kodKlasa": "21", "kodPodklasa": "Z"},
                            {"kodDzial": "61", "kodKlasa": "10", "kodPodklasa": "Z"},
                        ],
                    }
                },
            },
        }
    }


async def test_client_parses_safe_current_extract_fields() -> None:
    """Read name, legal form and PKD, while deliberately excluding NIP."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/krs/odpisaktualny/0000500605"
        assert request.headers["accept"] == "application/json"
        return httpx.Response(200, json=current_extract_payload())

    record = await KrsClient(
        "https://api-krs.ms.gov.pl", transport=httpx.MockTransport(handler)
    ).fetch_current_extract("500605")

    assert record.krs_number == "0000500605"
    assert record.name == "Example sp. z o.o."
    assert record.pkd_codes == ["61.10.Z", "43.21.Z"]
    assert record.registry_updated_on is not None


async def test_client_reports_not_found_and_malformed_payloads() -> None:
    """Do not turn absent or malformed public data into a guessed profile."""
    not_found = KrsClient(
        "https://api-krs.ms.gov.pl",
        transport=httpx.MockTransport(lambda _: httpx.Response(404)),
    )
    with pytest.raises(KrsNotFoundError):
        await not_found.fetch_current_extract("500605")

    malformed = KrsClient(
        "https://api-krs.ms.gov.pl",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
    )
    with pytest.raises(KrsSourceError, match="required company fields"):
        await malformed.fetch_current_extract("500605")
