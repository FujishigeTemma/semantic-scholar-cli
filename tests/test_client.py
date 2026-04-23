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


def test_get_citation_returns_bibtex(
    mocked_api,
    api_base_url: str,
    sample_paper: dict,
) -> None:
    mocked_api.get(f"{api_base_url}/paper/paper-123").mock(
        return_value=json_response(sample_paper)
    )
    client = SemanticScholarClient(base_url=api_base_url)

    response = client.get_citation(CitationGetInput(paper_id="paper-123"))

    assert response["format"] == "bibtex"
    assert response["citation"] == "@article{attention2017,...}"
    assert "availableFormats" not in response


def test_get_citation_raises_when_styles_empty(
    mocked_api,
    api_base_url: str,
    sample_paper: dict,
) -> None:
    sample_paper["citationStyles"] = {}
    mocked_api.get(f"{api_base_url}/paper/paper-123").mock(
        return_value=json_response(sample_paper)
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.get_citation(CitationGetInput(paper_id="paper-123"))

    assert exc_info.value.code == "no_citation_data"
    assert "hint" in (exc_info.value.details or {})


def test_404_on_paper_includes_paper_id_format_hint(
    mocked_api, api_base_url: str
) -> None:
    mocked_api.get(f"{api_base_url}/paper/missing").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client._request_json("paper/missing")

    assert exc_info.value.code == "not_found"
    assert exc_info.value.exit_code == 4
    hint = (exc_info.value.details or {}).get("hint", "")
    assert "DOI:" in hint and "ARXIV:" in hint


def test_404_on_author_includes_author_id_hint(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/author/missing").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client._request_json("author/missing")

    hint = (exc_info.value.details or {}).get("hint", "")
    assert "numeric" in hint


def test_401_maps_to_auth_error_with_api_key_hint(
    mocked_api, api_base_url: str
) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(401, json={"message": "unauthorized"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert exc_info.value.code == "auth_error"
    assert "SEMANTIC_SCHOLAR_API_KEY" in (exc_info.value.details or {}).get("hint", "")


def test_429_without_key_hints_to_set_api_key(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(429, json={"message": "slow down"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert exc_info.value.code == "rate_limited"
    assert "SEMANTIC_SCHOLAR_API_KEY" in (exc_info.value.details or {}).get("hint", "")


def test_429_with_key_hints_to_reduce_rate(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(429, json={"message": "slow down"})
    )
    client = SemanticScholarClient(base_url=api_base_url, api_key="some-key")

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert "Reduce" in (exc_info.value.details or {}).get("hint", "")


def test_400_maps_to_bad_request_with_help_hint(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(400, json={"message": "bad year"})
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert exc_info.value.code == "bad_request"
    assert "--help" in (exc_info.value.details or {}).get("hint", "")


def test_invalid_json_maps_to_upstream_error(mocked_api, api_base_url: str) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=httpx.Response(200, text="not-json")
    )
    client = SemanticScholarClient(base_url=api_base_url)

    with pytest.raises(SemanticScholarError) as exc_info:
        client.search_papers(PaperSearchInput(query="test"))

    assert exc_info.value.code == "upstream_error"
