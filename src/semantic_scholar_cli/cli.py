"""Typer-based CLI for Semantic Scholar."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import typer
from pydantic import ValidationError

from .client import SemanticScholarClient
from .contracts import (
    AuthorGetInput,
    AuthorSearchInput,
    CitationGetInput,
    PaperAuthorsInput,
    PaperEdgeInput,
    PaperGetInput,
    PaperSearchInput,
)
from .errors import SemanticScholarError
from .tooling import TOOL_SPECS

app = typer.Typer(
    help="CLI-first Semantic Scholar tooling for LLM workflows.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
)
paper_app = typer.Typer(help="Read-only paper operations.", no_args_is_help=True)
author_app = typer.Typer(help="Read-only author operations.", no_args_is_help=True)
citation_app = typer.Typer(help="Formatted citation export.", no_args_is_help=True)
tool_app = typer.Typer(help="Model-facing command metadata.", no_args_is_help=True)

app.add_typer(paper_app, name="paper")
app.add_typer(author_app, name="author")
app.add_typer(citation_app, name="citation")
app.add_typer(tool_app, name="tool")

ModelT = TypeVar("ModelT")


@dataclass(slots=True)
class AppSettings:
    """Process-wide CLI settings."""

    api_key: str | None
    base_url: str
    timeout: float
    pretty: bool


@app.callback()
def main_callback(
    ctx: typer.Context,
    api_key: str | None = typer.Option(
        default=None,
        envvar="SEMANTIC_SCHOLAR_API_KEY",
        help="Semantic Scholar API key.",
    ),
    base_url: str = typer.Option(
        default="https://api.semanticscholar.org/graph/v1",
        help="Semantic Scholar Graph API base URL.",
    ),
    timeout: float = typer.Option(
        default=20.0,
        min=1.0,
        help="HTTP timeout in seconds.",
    ),
    pretty: bool = typer.Option(
        default=False,
        help="Pretty-print JSON output for humans.",
    ),
) -> None:
    """Initialize shared settings."""
    ctx.obj = AppSettings(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        pretty=pretty,
    )


@paper_app.command("search")
def paper_search(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query", help="Plain-text query."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
    limit: int = typer.Option(10, min=1, max=100),
    offset: int = typer.Option(0, min=0),
    year: str | None = typer.Option(None, help="Publication year or range."),
    publication_date_or_year: str | None = typer.Option(
        None,
        "--publication-date-or-year",
        help="Publication date range or year range accepted by Semantic Scholar.",
    ),
    field_of_study: list[str] | None = typer.Option(
        None,
        "--field-of-study",
        help="Repeat to filter by field of study.",
    ),
    venue: list[str] | None = typer.Option(None, help="Repeat to filter by venue."),
    publication_type: list[str] | None = typer.Option(
        None,
        "--publication-type",
        help="Repeat to filter by publication type.",
    ),
    open_access_pdf: bool = typer.Option(
        False,
        "--open-access-pdf",
        help="Restrict results to papers with an open access PDF.",
    ),
    min_citation_count: int | None = typer.Option(
        None,
        "--min-citation-count",
        min=0,
        help="Restrict results to papers at or above this citation count.",
    ),
) -> None:
    """Search papers."""

    _run_command(
        ctx,
        PaperSearchInput,
        {
            "query": query,
            "fields": field,
            "limit": limit,
            "offset": offset,
            "year": year,
            "publication_date_or_year": publication_date_or_year,
            "fields_of_study": field_of_study,
            "venue": venue,
            "publication_types": publication_type,
            "open_access_pdf": open_access_pdf,
            "min_citation_count": min_citation_count,
        },
        lambda client, request: _normalize_page(
            client.search_papers(request),
            item_key="papers",
        ),
    )


@paper_app.command("get")
def paper_get(
    ctx: typer.Context,
    paper_id: str = typer.Option(..., "--paper-id", help="Semantic Scholar paper identifier."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
) -> None:
    """Get paper details."""

    _run_command(
        ctx,
        PaperGetInput,
        {"paper_id": paper_id, "fields": field},
        lambda client, request: {
            "data": _snake_case_keys(client.get_paper(request)),
            "meta": {
                "paper_id": paper_id,
                "source": "semantic_scholar_graph_api",
            },
        },
    )


@paper_app.command("authors")
def paper_authors(
    ctx: typer.Context,
    paper_id: str = typer.Option(..., "--paper-id", help="Semantic Scholar paper identifier."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
    limit: int = typer.Option(25, min=1, max=1000),
    offset: int = typer.Option(0, min=0),
) -> None:
    """List authors for a paper."""

    _run_command(
        ctx,
        PaperAuthorsInput,
        {
            "paper_id": paper_id,
            "fields": field,
            "limit": limit,
            "offset": offset,
        },
        lambda client, request: _normalize_page(
            client.get_paper_authors(request),
            item_key="authors",
            extra_meta={"paper_id": paper_id},
        ),
    )


@paper_app.command("citations")
def paper_citations(
    ctx: typer.Context,
    paper_id: str = typer.Option(..., "--paper-id", help="Semantic Scholar paper identifier."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
    limit: int = typer.Option(10, min=1, max=1000),
    offset: int = typer.Option(0, min=0),
) -> None:
    """List papers that cite a paper."""

    _run_command(
        ctx,
        PaperEdgeInput,
        {"paper_id": paper_id, "fields": field, "limit": limit, "offset": offset},
        lambda client, request: _normalize_edge_page(
            client.get_paper_citations(request),
            edge_key="citingPaper",
            item_key="citations",
            paper_id=paper_id,
        ),
    )


@paper_app.command("references")
def paper_references(
    ctx: typer.Context,
    paper_id: str = typer.Option(..., "--paper-id", help="Semantic Scholar paper identifier."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
    limit: int = typer.Option(10, min=1, max=1000),
    offset: int = typer.Option(0, min=0),
) -> None:
    """List papers referenced by a paper."""

    _run_command(
        ctx,
        PaperEdgeInput,
        {"paper_id": paper_id, "fields": field, "limit": limit, "offset": offset},
        lambda client, request: _normalize_edge_page(
            client.get_paper_references(request),
            edge_key="citedPaper",
            item_key="references",
            paper_id=paper_id,
        ),
    )


@author_app.command("search")
def author_search(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query", help="Author name query."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
    limit: int = typer.Option(10, min=1, max=100),
    offset: int = typer.Option(0, min=0),
) -> None:
    """Search authors."""

    _run_command(
        ctx,
        AuthorSearchInput,
        {"query": query, "fields": field, "limit": limit, "offset": offset},
        lambda client, request: _normalize_page(
            client.search_authors(request),
            item_key="authors",
        ),
    )


@author_app.command("get")
def author_get(
    ctx: typer.Context,
    author_id: str = typer.Option(..., "--author-id", help="Semantic Scholar author identifier."),
    field: list[str] | None = typer.Option(None, "--field", help="Repeat to request extra fields."),
) -> None:
    """Get author details."""

    _run_command(
        ctx,
        AuthorGetInput,
        {"author_id": author_id, "fields": field},
        lambda client, request: {
            "data": _snake_case_keys(client.get_author(request)),
            "meta": {
                "author_id": author_id,
                "source": "semantic_scholar_graph_api",
            },
        },
    )


@citation_app.command("get")
def citation_get(
    ctx: typer.Context,
    paper_id: str = typer.Option(..., "--paper-id", help="Semantic Scholar paper identifier."),
    format: str = typer.Option("bibtex", "--format", help="Citation format."),
    include_abstract: bool = typer.Option(
        False,
        "--include-abstract",
        help="Include abstract when present.",
    ),
) -> None:
    """Get a formatted citation."""

    _run_command(
        ctx,
        CitationGetInput,
        {
            "paper_id": paper_id,
            "format": format,
            "include_abstract": include_abstract,
        },
        lambda client, request: {
            "data": _snake_case_keys(client.get_citation(request)),
            "meta": {
                "paper_id": paper_id,
                "source": "semantic_scholar_graph_api",
            },
        },
    )


@tool_app.command("list")
def tool_list(ctx: typer.Context) -> None:
    """List model-facing command metadata."""

    specs = [tool.to_dict() for tool in TOOL_SPECS]
    _emit(
        settings=_settings(ctx),
        payload=_success_payload(
            data={"tools": specs},
            meta={"count": len(specs), "source": "semantic_scholar_cli"},
        ),
    )


def _run_command(
    ctx: typer.Context,
    model_cls: type[ModelT],
    raw_input: dict[str, Any],
    action: Callable[[SemanticScholarClient, ModelT], dict[str, Any]],
) -> None:
    settings = _settings(ctx)
    client = SemanticScholarClient(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout,
    )

    try:
        request = model_cls.model_validate(raw_input)
        result = action(client, request)
        payload = _success_payload(data=result["data"], meta=result["meta"])
        _emit(settings, payload)
    except ValidationError as exc:
        _emit(
            settings,
            _error_payload(
                code="invalid_input",
                message="Command input failed validation.",
                details={"errors": exc.errors()},
            ),
        )
        raise typer.Exit(2) from exc
    except SemanticScholarError as exc:
        _emit(
            settings,
            _error_payload(exc.code, exc.message, exc.details),
        )
        raise typer.Exit(exc.exit_code) from exc


def _settings(ctx: typer.Context) -> AppSettings:
    settings = ctx.obj
    if not isinstance(settings, AppSettings):
        raise RuntimeError("CLI settings were not initialized.")
    return settings


def _normalize_page(
    response: dict[str, Any],
    *,
    item_key: str,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = response.get("data") or []
    if not isinstance(data, list):
        data = []

    meta: dict[str, Any] = {
        "count": len(data),
        "offset": response.get("offset", 0),
        "next_offset": response.get("next"),
        "total": response.get("total"),
        "source": "semantic_scholar_graph_api",
    }
    if extra_meta:
        meta.update(extra_meta)

    return {
        "data": {item_key: _snake_case_keys(data)},
        "meta": meta,
    }


def _normalize_edge_page(
    response: dict[str, Any],
    *,
    edge_key: str,
    item_key: str,
    paper_id: str,
) -> dict[str, Any]:
    items = response.get("data") or []
    normalized_items: list[dict[str, Any]] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            paper_payload = item.get(edge_key) or {}
            normalized_item: dict[str, Any] = {"paper": _snake_case_keys(paper_payload)}
            for key, value in item.items():
                if key == edge_key:
                    continue
                normalized_item[_to_snake_case(key)] = _snake_case_keys(value)
            normalized_items.append(normalized_item)

    return {
        "data": {item_key: normalized_items},
        "meta": {
            "count": len(normalized_items),
            "offset": response.get("offset", 0),
            "next_offset": response.get("next"),
            "paper_id": paper_id,
            "source": "semantic_scholar_graph_api",
        },
    }


def _success_payload(data: Any, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "meta": _snake_case_keys(meta),
    }


def _error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": _snake_case_keys(details or {}),
        },
        "meta": {
            "source": "semantic_scholar_cli",
        },
    }


def _emit(settings: AppSettings, payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2 if settings.pretty else None)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _snake_case_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {_to_snake_case(str(key)): _snake_case_keys(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_snake_case_keys(item) for item in value]
    return value


def _to_snake_case(value: str) -> str:
    value = value.replace("-", "_").replace(" ", "_")
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()


def main() -> None:
    """CLI entrypoint."""
    app()
