"""Tests for the Semantic Scholar API client."""

from __future__ import annotations

import httpx
import pytest

from semantic_scholar_cli.client import SemanticScholarClient
from semantic_scholar_cli.contracts import CitationGetInput, PaperSearchInput
from semantic_scholar_cli.errors import SemanticScholarError
from tests.conftest import json_response


def test_search_papers_serializes_repeatable_fields(
    mocked_api,
    api_base_url: str,
    sample_search_response: dict,
) -> None:
    route = mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=json_response(sample_search_response)
    )
    client = SemanticScholarClient(base_url=api_base_url)

    response = client.search_papers(
        PaperSearchInput(
            query="transformer",
            fields=["title", "abstract"],
            open_access_pdf=True,
            fields_of_study=["Computer Science", "Mathematics"],
        )
    )

    assert response["total"] == 1
    assert route.called
    request = route.calls[0].request
    assert request.url.params["fields"] == "title,abstract"
    assert request.url.params["fieldsOfStudy"] == "Computer Science,Mathematics"
    assert "openAccessPdf" in request.url.params


def test_get_citation_extracts_requested_format(
    mocked_api,
    api_base_url: str,
    sample_paper: dict,
) -> None:
    mocked_api.get(f"{api_base_url}/paper/paper-123").mock(
        return_value=json_response(sample_paper)
    )
    client = SemanticScholarClient(base_url=api_base_url)

    response = client.get_citation(CitationGetInput(paper_id="paper-123", format="apa"))

    assert response["format"] == "apa"
    assert "Vaswani" in response["citation"]
    assert response["availableFormats"] == ["apa", "bibtex"]


def test_get_citation_raises_if_format_missing(
    mocked_api,
    api_base_url: str,
    sample_paper: dict,
) -> None:
    sample_paper["citationStyles"] = {"bibtex": "@article{attention2017,...}"}
    mocked_api.get(f"{api_base_url}/paper/paper-123").mock(
        return_value=json_response(sample_paper)
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.get_citation(CitationGetInput(paper_id="paper-123", format="mla"))

    assert exc_info.value.code == "upstream_error"


def test_404_maps_to_not_found(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/missing").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client._request_json("paper/missing")

    assert exc_info.value.code == "not_found"
    assert exc_info.value.exit_code == 4


def test_invalid_json_maps_to_upstream_error(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(200, text="not-json")
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert exc_info.value.code == "upstream_error"
