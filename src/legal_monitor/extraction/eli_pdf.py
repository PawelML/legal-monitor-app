"""Official ELI PDF source adapter."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from legal_monitor.eli.client import Publisher


@dataclass(frozen=True, slots=True)
class DownloadedPdf:
    """A PDF body with the canonical official source URL."""

    source_url: str
    content: bytes


class ELIPdfClient:
    """Download official act PDFs using the documented ELI URL format."""

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def download(
        self, publisher: Publisher, year: int, position: int
    ) -> DownloadedPdf:
        """Fetch one PDF and reject non-successful or empty responses."""
        path = f"/acts/{publisher}/{year}/{position}/text.pdf"
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            transport=self._transport,
        ) as client:
            response = await client.get(path)
            response.raise_for_status()
        if not response.content:
            raise ValueError("ELI returned an empty PDF response")
        return DownloadedPdf(
            source_url=f"{self._base_url}{path}", content=response.content
        )
