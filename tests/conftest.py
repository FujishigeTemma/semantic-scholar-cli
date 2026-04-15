"""Test fixtures for semantic-scholar-cli."""

from __future__ import annotations

import pytest
import respx
from httpx import Response


@pytest.fixture
def api_base_url() -> str:
    return "https://api.test/graph/v1"


@pytest.fixture
def mocked_api() -> respx.MockRouter:
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def sample_paper() -> dict:
    return {
        "paperId": "paper-123",
        "title": "Attention Is All You Need",
        "abstract": "Transformer architecture.",
        "year": 2017,
        "venue": "NIPS",
        "authors": [{"authorId": "author-1", "name": "Ashish Vaswani"}],
        "citationCount": 99999,
        "referenceCount": 42,
        "fieldsOfStudy": ["Computer Science"],
        "publicationDate": "2017-06-12",
        "openAccessPdf": {"url": "https://example.test/paper.pdf"},
        "citationStyles": {
            "bibtex": "@article{attention2017,...}",
            "apa": "Vaswani et al. (2017). Attention Is All You Need.",
        },
    }


@pytest.fixture
def sample_search_response(sample_paper: dict) -> dict:
    return {
        "total": 1,
        "offset": 0,
        "next": 1,
        "data": [sample_paper],
    }


@pytest.fixture
def sample_authors_response() -> dict:
    return {
        "offset": 0,
        "next": None,
        "data": [
            {
                "authorId": "author-1",
                "name": "Ashish Vaswani",
                "affiliations": ["Google Brain"],
                "citationCount": 123456,
                "hIndex": 99,
                "paperCount": 100,
            }
        ],
    }


@pytest.fixture
def sample_edges_response(sample_paper: dict) -> dict:
    return {
        "offset": 0,
        "next": 1,
        "data": [
            {
                "contexts": ["Builds on transformer work."],
                "intents": ["background"],
                "isInfluential": True,
                "citingPaper": sample_paper,
            }
        ],
    }


def json_response(payload: dict, status_code: int = 200) -> Response:
    return Response(status_code, json=payload)
