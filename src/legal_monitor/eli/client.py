"""Typed client for yearly act metadata from the official ELI API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

Publisher = Literal["DU", "MP"]


class ELIActPayload(BaseModel):
    """The required subset of one documented yearly-list item."""

    model_config = ConfigDict(populate_by_name=True)

    eli: str = Field(alias="ELI")
    address: str
    announcement_date: date | None = Field(default=None, alias="announcementDate")
    change_date: datetime | None = Field(default=None, alias="changeDate")
    display_address: str = Field(alias="displayAddress")
    position: int = Field(alias="pos")
    promulgation_date: date | None = Field(default=None, alias="promulgation")
    publisher: Publisher
    status: str
    text_html: bool = Field(alias="textHTML")
    text_pdf: bool = Field(alias="textPDF")
    title: str
    act_type: str = Field(alias="type")
    volume: int
    year: int


class ELIListPayload(BaseModel):
    """The documented response body for a yearly act list."""

    count: int
    items: list[ELIActPayload]


@dataclass(frozen=True, slots=True)
class ELIActRecord:
    """Validated act metadata ready for persistence."""

    eli: str
    address: str
    announcement_date: date | None
    change_date: datetime | None
    display_address: str
    position: int
    promulgation_date: date | None
    publisher: Publisher
    status: str
    has_text_html: bool
    has_text_pdf: bool
    title: str
    act_type: str
    volume: int
    year: int
    raw_metadata: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: ELIActPayload) -> ELIActRecord:
        """Normalize source timestamps while preserving all source fields."""
        change_date = payload.change_date
        if change_date is not None and change_date.tzinfo is None:
            change_date = change_date.replace(tzinfo=UTC)
        return cls(
            eli=payload.eli,
            address=payload.address,
            announcement_date=payload.announcement_date,
            change_date=change_date,
            display_address=payload.display_address,
            position=payload.position,
            promulgation_date=payload.promulgation_date,
            publisher=payload.publisher,
            status=payload.status,
            has_text_html=payload.text_html,
            has_text_pdf=payload.text_pdf,
            title=payload.title,
            act_type=payload.act_type,
            volume=payload.volume,
            year=payload.year,
            raw_metadata=payload.model_dump(by_alias=True, mode="json"),
        )


class ELIClient:
    """Fetch and validate official ELI act-list responses without retries."""

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def list_acts(self, publisher: Publisher, year: int) -> list[ELIActRecord]:
        """Return validated metadata for one publisher and year."""
        if publisher not in ("DU", "MP"):
            raise ValueError("publisher must be DU or MP")
        if year < 1918 or year > 9999:
            raise ValueError("year must be between 1918 and 9999")

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Accept": "application/json"},
            timeout=timeout,
            transport=self._transport,
        ) as client:
            response = await client.get(f"/acts/{publisher}/{year}")
            response.raise_for_status()

        payload = ELIListPayload.model_validate(response.json())
        if payload.count != len(payload.items):
            raise ValueError("ELI response count does not match the number of items")
        records = [ELIActRecord.from_payload(item) for item in payload.items]
        has_unexpected_record = any(
            record.publisher != publisher or record.year != year for record in records
        )
        if has_unexpected_record:
            raise ValueError("ELI response contains an unexpected publisher or year")
        return records
