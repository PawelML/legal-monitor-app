"""Explicit analysis command using a fixture or the approved OpenAI pilot."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from legal_monitor.analysis.providers import (
    AnalysisProvider,
    OpenAIAnalysisProvider,
    StaticAnalysisProvider,
)
from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.services.act_analysis import ActAnalysisService


def parse_args() -> argparse.Namespace:
    """Parse analysis options and require explicit consent for live calls."""
    parser = argparse.ArgumentParser(description="Persist one validated act analysis.")
    parser.add_argument("--act-eli", required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument(
        "--provider",
        choices=("fixture", "openai"),
        default="fixture",
        help="Use the offline fixture provider (default) or the approved OpenAI pilot.",
    )
    parser.add_argument(
        "--response-file",
        type=Path,
        help="Local JSON response fixture, required only with --provider fixture.",
    )
    parser.add_argument(
        "--allow-live-call",
        action="store_true",
        help="Required with --provider openai because it sends the selected act text.",
    )
    args = parser.parse_args()
    if args.provider == "fixture" and args.response_file is None:
        parser.error("--response-file is required with --provider fixture")
    if args.provider == "openai" and not args.allow_live_call:
        parser.error("--allow-live-call is required with --provider openai")
    return args


async def run(
    act_eli: str,
    prompt_version: str,
    provider_name: str,
    response_file: Path | None,
) -> int:
    """Validate and persist an analysis from the selected explicit provider."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        if provider_name == "fixture":
            assert response_file is not None
            provider: AnalysisProvider = StaticAnalysisProvider(
                response_file.read_text(encoding="utf-8")
            )
        else:
            if (
                settings.openai_api_key is None
                or settings.openai_analysis_instructions is None
            ):
                raise ValueError(
                    "OPENAI_API_KEY and OPENAI_ANALYSIS_INSTRUCTIONS are required"
                )
            provider = OpenAIAnalysisProvider(
                api_key=settings.openai_api_key.get_secret_value(),
                instructions=settings.openai_analysis_instructions.get_secret_value(),
                model_name=settings.openai_model,
                reasoning_effort=settings.openai_reasoning_effort,
            )
        result = await ActAnalysisService(
            create_session_factory(engine), provider
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
    return asyncio.run(
        run(args.act_eli, args.prompt_version, args.provider, args.response_file)
    )


if __name__ == "__main__":
    raise SystemExit(main())
