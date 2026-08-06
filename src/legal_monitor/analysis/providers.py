"""Provider boundary; production model adapters are intentionally deferred."""

from __future__ import annotations

from typing import Protocol


class AnalysisProvider(Protocol):
    """Return one JSON document for the supplied extracted act text."""

    model_name: str

    async def analyse(self, text: str, prompt_version: str) -> str:
        """Produce schema-compatible JSON without performing persistence."""


class StaticAnalysisProvider:
    """Deterministic test double returning a predefined JSON document."""

    model_name = "test-static-provider"

    def __init__(self, response: str) -> None:
        self._response = response

    async def analyse(self, text: str, prompt_version: str) -> str:
        """Return the fixture response while retaining the provider contract."""
        del text, prompt_version
        return self._response
