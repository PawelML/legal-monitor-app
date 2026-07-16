"""Explicit command-line entry point for Phase 0 metadata imports."""

from __future__ import annotations

import argparse
import asyncio

from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.eli.client import ELIClient, Publisher
from legal_monitor.services.ingestion import MetadataIngestionService


def parse_args() -> argparse.Namespace:
    """Parse the intentionally small, explicit import command interface."""
    parser = argparse.ArgumentParser(description="Import ELI act metadata.")
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument(
        "--publisher",
        action="append",
        choices=("DU", "MP"),
        help="Import only this publisher; repeat to select both.",
    )
    return parser.parse_args()


async def run(year: int, publishers: tuple[Publisher, ...]) -> int:
    """Run one import and return a shell-friendly status code."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        service = MetadataIngestionService(
            create_session_factory(engine), ELIClient(settings.eli_base_url)
        )
        result = await service.import_year(year, publishers)
    except Exception as exc:
        print(f"ELI import failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        await engine.dispose()

    print(
        "ELI import succeeded: "
        f"job={result.job_run_id} input={result.input_count} "
        f"created={result.created_count} updated={result.updated_count}"
    )
    return 0


def main() -> int:
    """Execute the command synchronously for Python module invocation."""
    args = parse_args()
    publishers = tuple(args.publisher or ("DU", "MP"))
    return asyncio.run(run(args.year, publishers))


if __name__ == "__main__":
    raise SystemExit(main())
