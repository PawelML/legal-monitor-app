"""Strict output schema and evidence checks for model responses."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from legal_monitor.analysis.taxonomy import TAGS_V1, TAXONOMY_VERSION, TaxonomyTag

ANALYSIS_SCHEMA_VERSION = "v1"


class Evidence(BaseModel):
    """A short quotation grounding one analysis claim in a source page."""

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(ge=1)
    quote: str = Field(min_length=3, max_length=500)


class AnalysisOutput(BaseModel):
    """The only LLM output shape accepted for persistence."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary_pl: str = Field(min_length=20, max_length=3000)
    business_relevant: bool
    affected_parties: list[str] = Field(max_length=12)
    tags: list[TaxonomyTag] = Field(max_length=12)
    obligations: list[str] = Field(max_length=12)
    effective_from: date | None = None
    impact_level: int = Field(ge=1, le=5)
    evidence: list[Evidence] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_business_relevance(self) -> AnalysisOutput:
        """Reject ungrounded taxonomy and contradictory relevance claims."""
        unknown_tags = set(self.tags).difference(TAGS_V1)
        if unknown_tags:
            raise ValueError(f"unknown taxonomy tags: {sorted(unknown_tags)}")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must not contain duplicates")
        if not self.business_relevant and (self.tags or self.obligations):
            raise ValueError("non-relevant acts cannot contain tags or obligations")
        return self


def validate_evidence(output: AnalysisOutput, pages: list[str]) -> None:
    """Ensure every stored quotation appears on the declared source page."""
    for item in output.evidence:
        if item.page > len(pages) or (
            normalise_evidence_text(item.quote)
            not in normalise_evidence_text(pages[item.page - 1])
        ):
            raise ValueError("evidence quote is not present on its declared page")


def normalise_evidence_text(text: str) -> str:
    """Compare extracted PDF quotations independent of line-wrap whitespace."""
    return " ".join(text.split())


def analysis_provenance() -> tuple[str, str]:
    """Return versions stored alongside every accepted analysis."""
    return ANALYSIS_SCHEMA_VERSION, TAXONOMY_VERSION
