"""Small, explicit taxonomy used by the first analysis version."""

from __future__ import annotations

from typing import Literal

TAXONOMY_VERSION = "v1"

TaxonomyTag = Literal[
    "taxes_vat",
    "employment",
    "payroll",
    "health_and_safety",
    "data_protection",
    "ecommerce",
    "food",
    "transport",
    "construction",
    "environment",
    "finance_reporting",
    "consumer_protection",
]

TAGS_V1 = frozenset(
    {
        "taxes_vat",
        "employment",
        "payroll",
        "health_and_safety",
        "data_protection",
        "ecommerce",
        "food",
        "transport",
        "construction",
        "environment",
        "finance_reporting",
        "consumer_protection",
    }
)
