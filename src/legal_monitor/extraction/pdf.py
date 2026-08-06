"""Deterministic local PDF extraction without OCR."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

import pdfplumber

EXTRACTOR_VERSION = "pdfplumber-v1"


@dataclass(frozen=True, slots=True)
class ExtractedPdfText:
    """Normalised page text and its reproducible content hash."""

    pages: list[str]
    content: str
    content_hash: str


def extract_pdf_text(pdf_bytes: bytes) -> ExtractedPdfText:
    """Extract non-empty text from every PDF page or fail explicitly."""
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        pages = [((page.extract_text() or "").strip()) for page in document.pages]
    if not pages or any(not page for page in pages):
        raise ValueError("PDF contains an empty or image-only page")
    content = "\n\n".join(pages)
    return ExtractedPdfText(
        pages=pages,
        content=content,
        content_hash=sha256(content.encode("utf-8")).hexdigest(),
    )
