"""Explicit local analysis command using a supplied deterministic response."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from legal_monitor.analysis.providers import StaticAnalysisProvider
from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.services.act_analysis import ActAnalysisService


def parse_args() -> argparse.Namespace:
    """Parse a safe command that cannot accidentally make a provider call."""
    parser = argparse.ArgumentParser(description="Persist one validated act analysis.")
    parser.add_argument("--act-eli", required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument(
        "--response-file",
        type=Path,
        required=True,
        help="Local JSON response fixture; real model support requires its ADR.",
    )
    return parser.parse_args()


async def run(act_eli: str, prompt_version: str, response_file: Path) -> int:
    """Validate and persist a local fixture response for one extracted act."""
    engine = create_engine(get_settings().database_url)
    try:
        response = response_file.read_text(encoding="utf-8")
        result = await ActAnalysisService(
            create_session_factory(engine), StaticAnalysisProvider(response)
        ).analyse(act_eli, prompt_version)
    except Exception as exc:
        print(f"Act analysis failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        await engine.dispose()
    print(
        f"Act analysis succeeded: job={result.job_run_id} analysis={result.analysis_id}"
    )
    return 0


def main() -> int:
    """Execute the command synchronously for Python module invocation."""
    args = parse_args()
    return asyncio.run(run(args.act_eli, args.prompt_version, args.response_file))


if __name__ == "__main__":
    raise SystemExit(main())
