"""Error types for Semantic Scholar CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SemanticScholarError(Exception):
    """Structured error surfaced to CLI callers."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    exit_code: int = 1

    def __str__(self) -> str:
        return self.message
