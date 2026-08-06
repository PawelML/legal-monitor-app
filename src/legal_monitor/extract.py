"""Explicit command for extracting text from one official ELI PDF."""

from __future__ import annotations

import argparse
import asyncio

from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.extraction.eli_pdf import ELIPdfClient
from legal_monitor.services.text_extraction import TextExtractionService


def parse_args() -> argparse.Namespace:
    """Parse an intentionally explicit one-act extraction command."""
    parser = argparse.ArgumentParser(description="Extract text from an ELI act PDF.")
    parser.add_argument("--act-eli", required=True)
    return parser.parse_args()


async def run(act_eli: str) -> int:
    """Extract one act text and return a shell-friendly exit status."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        result = await TextExtractionService(
            create_session_factory(engine), ELIPdfClient(settings.eli_base_url)
        ).extract(act_eli)
    except Exception as exc:
        print(f"Text extraction failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        await engine.dispose()
    print(
        "Text extraction succeeded: "
        f"job={result.job_run_id} text={result.act_text_id} created={result.created}"
    )
    return 0


def main() -> int:
    """Execute the command synchronously for Python module invocation."""
    return asyncio.run(run(parse_args().act_eli))


if __name__ == "__main__":
    raise SystemExit(main())
