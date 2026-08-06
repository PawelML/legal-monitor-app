"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from legal_monitor.config import get_settings
from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.krs.client import KrsClient, KrsNotFoundError, KrsSourceError
from legal_monitor.models import CompanyProfile
from legal_monitor.services.company_profiles import CompanyProfileService
from legal_monitor.services.matching import MatchingPreviewService


class ProfileRefreshRequest(BaseModel):
    """Caller-selected monitoring tags for a public KRS profile refresh."""

    model_config = ConfigDict(extra="forbid")

    monitoring_tags: list[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    """Safe API projection of a company profile."""

    id: str
    krs_number: str
    name: str
    legal_form: str
    pkd_codes: list[str]
    monitoring_tags: list[str]
    registry_updated_on: date | None
    refreshed_at: datetime


class PreviewMatchResponse(BaseModel):
    """One explainable tag intersection from the non-deliverable preview."""

    act_eli: str
    act_title: str
    analysis_id: str
    shared_tags: list[str]


class MatchingPreviewResponse(BaseModel):
    """Response from a transient matching preview."""

    job_run_id: str
    matches: list[PreviewMatchResponse]


def _profile_response(profile: CompanyProfile) -> ProfileResponse:
    """Build a projection that excludes raw registry data and personal fields."""
    return ProfileResponse(
        id=profile.id,
        krs_number=profile.krs_number,
        name=profile.name,
        legal_form=profile.legal_form,
        pkd_codes=profile.pkd_codes,
        monitoring_tags=profile.monitoring_tags,
        registry_updated_on=profile.registry_updated_on,
        refreshed_at=profile.refreshed_at,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and dispose of database resources with the application."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    app.state.database_engine = engine
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    """Build the HTTP application without opening a database connection yet."""
    app = FastAPI(title="PrawoRadar", version="0.0.0", lifespan=lifespan)
    app.state.krs_client = KrsClient(get_settings().krs_base_url)

    @app.get("/health")
    async def health(request: Request) -> dict[str, str]:
        """Report readiness only after a minimal database round trip."""
        try:
            async with request.app.state.session_factory() as session:
                await session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            ) from exc
        return {"status": "ok"}

    @app.put("/profiles/krs/{krs_number}", response_model=ProfileResponse)
    async def refresh_profile(
        krs_number: str, payload: ProfileRefreshRequest, request: Request
    ) -> ProfileResponse:
        """Create or refresh a public KRS company profile by KRS number."""
        service = CompanyProfileService(
            request.app.state.session_factory, request.app.state.krs_client
        )
        try:
            result = await service.refresh_from_krs(krs_number, payload.monitoring_tags)
        except KrsNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except KrsSourceError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="KRS source unavailable",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        profile = await service.get_profile(result.profile_id)
        assert profile is not None
        return _profile_response(profile)

    @app.get("/profiles/{profile_id}", response_model=ProfileResponse)
    async def get_profile(profile_id: str, request: Request) -> ProfileResponse:
        """Read a safe stored profile without an external KRS request."""
        profile = await CompanyProfileService(
            request.app.state.session_factory, request.app.state.krs_client
        ).get_profile(profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="profile not found"
            )
        return _profile_response(profile)

    @app.post(
        "/profiles/{profile_id}/matches:preview", response_model=MatchingPreviewResponse
    )
    async def preview_matches(
        profile_id: str, request: Request
    ) -> MatchingPreviewResponse:
        """Return an explainable review preview with no delivery side effects."""
        try:
            result = await MatchingPreviewService(
                request.app.state.session_factory
            ).preview(profile_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="profile not found"
            ) from exc
        return MatchingPreviewResponse(
            job_run_id=result.job_run_id,
            matches=[
                PreviewMatchResponse(
                    act_eli=match.act_eli,
                    act_title=match.act_title,
                    analysis_id=match.analysis_id,
                    shared_tags=match.shared_tags,
                )
                for match in result.matches
            ],
        )

    return app


app = create_app()
