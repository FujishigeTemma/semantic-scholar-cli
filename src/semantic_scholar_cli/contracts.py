"""Typed contracts shared by CLI commands and future tool adapters."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_PAPER_SEARCH_FIELDS = (
    "paperId",
    "title",
    "year",
    "venue",
    "authors",
    "citationCount",
)
DEFAULT_PAPER_GET_FIELDS = (
    "paperId",
    "title",
    "abstract",
    "year",
    "venue",
    "journal",
    "authors",
    "citationCount",
    "referenceCount",
    "fieldsOfStudy",
    "publicationDate",
    "openAccessPdf",
)
DEFAULT_AUTHOR_FIELDS = (
    "authorId",
    "name",
    "affiliations",
    "citationCount",
    "hIndex",
    "paperCount",
)
DEFAULT_EDGE_FIELDS = (
    "paperId",
    "title",
    "year",
    "venue",
    "authors",
    "citationCount",
)
DEFAULT_CITATION_FIELDS = (
    "paperId",
    "title",
    "year",
    "venue",
    "authors",
    "citationStyles",
)


def _normalize_multi_string(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        raw_items = [value]
    else:
        raw_items = list(value)

    normalized: list[str] = []
    for item in raw_items:
        if item is None:
            continue
        if not isinstance(item, str):
            raise TypeError(f"Expected a string value, got {type(item).__name__}")
        for part in item.split(","):
            cleaned = part.strip()
            if cleaned:
                normalized.append(cleaned)

    deduped = list(dict.fromkeys(normalized))
    return deduped or None


def _csv(values: list[str] | tuple[str, ...] | None) -> str | None:
    if not values:
        return None
    return ",".join(values)


class RequestModel(BaseModel):
    """Base request model with strict validation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PaperSearchInput(RequestModel):
    """Input for paper search."""

    query: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_PAPER_SEARCH_FIELDS))
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    year: str | None = None
    publication_date_or_year: str | None = None
    fields_of_study: list[str] | None = None
    venue: list[str] | None = None
    publication_types: list[str] | None = None
    open_access_pdf: bool = False
    min_citation_count: int | None = Field(default=None, ge=0)

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_PAPER_SEARCH_FIELDS)

    @field_validator("fields_of_study", "venue", "publication_types", mode="before")
    @classmethod
    def normalize_multi_strings(cls, value: Any) -> list[str] | None:
        return _normalize_multi_string(value)

    def to_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "query": self.query,
            "fields": _csv(self.fields),
            "limit": self.limit,
            "offset": self.offset,
        }
        if self.year:
            params["year"] = self.year
        if self.publication_date_or_year:
            params["publicationDateOrYear"] = self.publication_date_or_year
        if self.fields_of_study:
            params["fieldsOfStudy"] = _csv(self.fields_of_study)
        if self.venue:
            params["venue"] = _csv(self.venue)
        if self.publication_types:
            params["publicationTypes"] = _csv(self.publication_types)
        if self.open_access_pdf:
            params["openAccessPdf"] = ""
        if self.min_citation_count is not None:
            params["minCitationCount"] = self.min_citation_count
        return params


class PaperGetInput(RequestModel):
    """Input for paper details lookup."""

    paper_id: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_PAPER_GET_FIELDS))

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_PAPER_GET_FIELDS)

    def to_params(self) -> dict[str, Any]:
        return {"fields": _csv(self.fields)}


class PaperAuthorsInput(RequestModel):
    """Input for paper author listing."""

    paper_id: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_AUTHOR_FIELDS))
    limit: int = Field(default=25, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_AUTHOR_FIELDS)

    def to_params(self) -> dict[str, Any]:
        return {
            "fields": _csv(self.fields),
            "limit": self.limit,
            "offset": self.offset,
        }


class PaperEdgeInput(RequestModel):
    """Input for paper citation/reference traversal."""

    paper_id: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_EDGE_FIELDS))
    limit: int = Field(default=10, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_EDGE_FIELDS)

    def to_params(self) -> dict[str, Any]:
        return {
            "fields": _csv(self.fields),
            "limit": self.limit,
            "offset": self.offset,
        }


class AuthorSearchInput(RequestModel):
    """Input for author search."""

    query: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_AUTHOR_FIELDS))
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_AUTHOR_FIELDS)

    def to_params(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "fields": _csv(self.fields),
            "limit": self.limit,
            "offset": self.offset,
        }


class AuthorGetInput(RequestModel):
    """Input for author lookup."""

    author_id: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_AUTHOR_FIELDS))

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_AUTHOR_FIELDS)

    def to_params(self) -> dict[str, Any]:
        return {"fields": _csv(self.fields)}


class CitationGetInput(RequestModel):
    """Input for citation export."""

    paper_id: str = Field(min_length=1)
    include_abstract: bool = False
    fields: list[str] = Field(default_factory=lambda: list(DEFAULT_CITATION_FIELDS))

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any) -> list[str]:
        normalized = _normalize_multi_string(value)
        return normalized or list(DEFAULT_CITATION_FIELDS)

    def to_params(self) -> dict[str, Any]:
        fields = list(self.fields)
        if self.include_abstract and "abstract" not in fields:
            fields.append("abstract")
        return {"fields": _csv(fields)}
