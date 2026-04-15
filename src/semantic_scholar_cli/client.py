"""HTTP client for the Semantic Scholar Graph API."""

from __future__ import annotations

from typing import Any

import httpx

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


class SemanticScholarClient:
    """Thin, typed wrapper around the Semantic Scholar Graph API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.semanticscholar.org/graph/v1",
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search_papers(self, request: PaperSearchInput) -> dict[str, Any]:
        return self._request_json("paper/search", request.to_params())

    def get_paper(self, request: PaperGetInput) -> dict[str, Any]:
        return self._request_json(f"paper/{request.paper_id}", request.to_params())

    def get_paper_authors(self, request: PaperAuthorsInput) -> dict[str, Any]:
        return self._request_json(
            f"paper/{request.paper_id}/authors",
            request.to_params(),
        )

    def get_paper_citations(self, request: PaperEdgeInput) -> dict[str, Any]:
        return self._request_json(
            f"paper/{request.paper_id}/citations",
            request.to_params(),
        )

    def get_paper_references(self, request: PaperEdgeInput) -> dict[str, Any]:
        return self._request_json(
            f"paper/{request.paper_id}/references",
            request.to_params(),
        )

    def search_authors(self, request: AuthorSearchInput) -> dict[str, Any]:
        return self._request_json("author/search", request.to_params())

    def get_author(self, request: AuthorGetInput) -> dict[str, Any]:
        return self._request_json(f"author/{request.author_id}", request.to_params())

    def get_citation(self, request: CitationGetInput) -> dict[str, Any]:
        response = self._request_json(f"paper/{request.paper_id}", request.to_params())
        styles = response.get("citationStyles") or {}
        citation = styles.get(request.format.value)
        if not citation:
            raise SemanticScholarError(
                code="upstream_error",
                message=f"Semantic Scholar did not return a '{request.format.value}' citation.",
                details={
                    "paper_id": request.paper_id,
                    "available_formats": sorted(styles.keys()),
                },
                exit_code=6,
            )

        payload: dict[str, Any] = {
            "paperId": response.get("paperId", request.paper_id),
            "title": response.get("title"),
            "year": response.get("year"),
            "venue": response.get("venue"),
            "authors": response.get("authors"),
            "format": request.format.value,
            "availableFormats": sorted(styles.keys()),
            "citation": citation,
        }
        if request.include_abstract and response.get("abstract"):
            payload["abstract"] = response["abstract"]
        return payload

    def _request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        filtered_params = {key: value for key, value in (params or {}).items() if value is not None}
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            with httpx.Client(timeout=self.timeout, headers=headers) as client:
                response = client.get(url, params=filtered_params)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise SemanticScholarError(
                code="timeout",
                message="Semantic Scholar API request timed out.",
                details={"path": path},
                exit_code=7,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc.response, path) from exc
        except httpx.RequestError as exc:
            raise SemanticScholarError(
                code="network_error",
                message="Could not reach the Semantic Scholar API.",
                details={"path": path, "reason": str(exc)},
                exit_code=6,
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise SemanticScholarError(
                code="upstream_error",
                message="Semantic Scholar API returned invalid JSON.",
                details={"path": path},
                exit_code=6,
            ) from exc

        if not isinstance(payload, dict):
            raise SemanticScholarError(
                code="upstream_error",
                message="Semantic Scholar API returned an unexpected response shape.",
                details={"path": path, "response_type": type(payload).__name__},
                exit_code=6,
            )
        return payload

    def _map_http_error(
        self,
        response: httpx.Response,
        path: str,
    ) -> SemanticScholarError:
        status_code = response.status_code
        details = {
            "path": path,
            "status_code": status_code,
            "upstream_message": self._read_error_message(response),
        }

        if status_code == 404:
            return SemanticScholarError(
                code="not_found",
                message="Semantic Scholar resource was not found.",
                details=details,
                exit_code=4,
            )
        if status_code == 429:
            return SemanticScholarError(
                code="rate_limited",
                message="Semantic Scholar API rate limit exceeded.",
                details=details,
                exit_code=5,
            )

        return SemanticScholarError(
            code="upstream_error",
            message="Semantic Scholar API returned an error response.",
            details=details,
            exit_code=6,
        )

    @staticmethod
    def _read_error_message(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text.strip()

        if isinstance(body, dict):
            for key in ("error", "message"):
                value = body.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return response.text.strip()
