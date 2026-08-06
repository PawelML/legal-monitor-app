"""Small, defensive adapter for current extracts from the public KRS API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx


class KrsNotFoundError(ValueError):
    """Raised when the public registry has no current extract for a KRS number."""


class KrsSourceError(RuntimeError):
    """Raised when the public registry cannot provide a usable response."""


@dataclass(frozen=True, slots=True)
class KrsCompanyRecord:
    """Safe projection of one current public KRS extract."""

    krs_number: str
    name: str
    legal_form: str
    pkd_codes: list[str]
    registry_updated_on: date | None


def normalise_krs_number(value: str) -> str:
    """Normalise the public ten-digit KRS identifier without accepting aliases."""
    digits = value.strip()
    if not digits.isdigit() or not digits or len(digits) > 10:
        raise ValueError("KRS number must contain from 1 to 10 digits")
    return digits.zfill(10)


class KrsClient:
    """Fetch and parse only the public fields needed for a company profile."""

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def fetch_current_extract(self, krs_number: str) -> KrsCompanyRecord:
        """Return one typed current extract or a clear source error."""
        normalised_krs = normalise_krs_number(krs_number)
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            transport=self._transport,
        ) as client:
            try:
                response = await client.get(
                    f"/api/krs/odpisaktualny/{normalised_krs}",
                    headers={"accept": "application/json"},
                )
            except httpx.HTTPError as exc:
                raise KrsSourceError("KRS request failed") from exc
        if response.status_code == httpx.codes.NOT_FOUND:
            raise KrsNotFoundError(f"KRS record not found: {normalised_krs}")
        if response.is_error:
            raise KrsSourceError(f"KRS returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise KrsSourceError("KRS returned invalid JSON") from exc
        return _parse_current_extract(payload, normalised_krs)


def _parse_current_extract(payload: Any, requested_krs: str) -> KrsCompanyRecord:
    """Validate the subset of the current-extract JSON contract we depend on."""
    try:
        extract = payload["odpis"]
        header = extract["naglowekA"]
        entity = extract["dane"]["dzial1"]["danePodmiotu"]
        activities = extract["dane"]["dzial3"]["przedmiotDzialalnosci"]
        received_krs = header["numerKRS"]
        name = entity["nazwa"]
        legal_form = entity["formaPrawna"]
    except (KeyError, TypeError) as exc:
        raise KrsSourceError("KRS response misses required company fields") from exc
    if received_krs != requested_krs:
        raise KrsSourceError("KRS response does not match requested KRS number")
    if not isinstance(name, str) or not name.strip():
        raise KrsSourceError("KRS response has an invalid company name")
    if not isinstance(legal_form, str) or not legal_form.strip():
        raise KrsSourceError("KRS response has an invalid legal form")
    registry_updated_on = _parse_registry_date(header.get("stanZDnia"))
    pkd_codes = _pkd_codes(activities)
    return KrsCompanyRecord(
        krs_number=requested_krs,
        name=name.strip(),
        legal_form=legal_form.strip(),
        pkd_codes=pkd_codes,
        registry_updated_on=registry_updated_on,
    )


def _parse_registry_date(value: Any) -> date | None:
    """Read the optional Polish KRS state date without guessing formats."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise KrsSourceError("KRS response has an invalid registry date")
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError as exc:
        raise KrsSourceError("KRS response has an invalid registry date") from exc


def _pkd_codes(activities: Any) -> list[str]:
    """Extract unique PKD codes from principal and additional activities."""
    if not isinstance(activities, dict):
        raise KrsSourceError("KRS response has invalid PKD activities")
    records = [
        *activities.get("przedmiotPrzewazajacejDzialalnosci", []),
        *activities.get("przedmiotPozostalejDzialalnosci", []),
    ]
    if not all(isinstance(record, dict) for record in records):
        raise KrsSourceError("KRS response has invalid PKD records")
    codes: list[str] = []
    for record in records:
        parts = [
            record.get("kodDzial"),
            record.get("kodKlasa"),
            record.get("kodPodklasa"),
        ]
        if not all(isinstance(part, str) and part for part in parts):
            continue
        code = f"{parts[0]}.{parts[1]}.{parts[2]}"
        if code not in codes:
            codes.append(code)
    return codes
