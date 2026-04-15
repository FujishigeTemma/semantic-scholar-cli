"""CLI behavior tests."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from semantic_scholar_cli.cli import app
from tests.conftest import json_response

runner = CliRunner()


def test_paper_search_outputs_json_by_default(
    mocked_api,
    api_base_url: str,
    sample_search_response: dict,
) -> None:
    mocked_api.get(f"{api_base_url}/paper/search").mock(
        return_value=json_response(sample_search_response)
    )

    result = runner.invoke(
        app,
        [
            "--base-url",
            api_base_url,
            "paper",
            "search",
            "--query",
            "transformer",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["papers"][0]["paper_id"] == "paper-123"
    assert payload["meta"]["source"] == "semantic_scholar_graph_api"


def test_paper_citations_normalize_nested_paper_payload(
    mocked_api,
    api_base_url: str,
    sample_edges_response: dict,
) -> None:
    mocked_api.get(f"{api_base_url}/paper/paper-123/citations").mock(
        return_value=json_response(sample_edges_response)
    )

    result = runner.invoke(
        app,
        [
            "--base-url",
            api_base_url,
            "paper",
            "citations",
            "--paper-id",
            "paper-123",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    citation = payload["data"]["citations"][0]
    assert citation["paper"]["paper_id"] == "paper-123"
    assert citation["is_influential"] is True


def test_pretty_flag_indents_json(
    mocked_api,
    api_base_url: str,
    sample_paper: dict,
) -> None:
    mocked_api.get(f"{api_base_url}/paper/paper-123").mock(
        return_value=json_response(sample_paper)
    )

    result = runner.invoke(
        app,
        [
            "--base-url",
            api_base_url,
            "--pretty",
            "paper",
            "get",
            "--paper-id",
            "paper-123",
        ],
    )

    assert result.exit_code == 0
    assert '\n  "ok": true,' in result.stdout


def test_validation_errors_return_structured_json(api_base_url: str) -> None:
    result = runner.invoke(
        app,
        [
            "--base-url",
            api_base_url,
            "paper",
            "search",
            "--query",
            "",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_input"


def test_tool_list_surfaces_model_metadata() -> None:
    result = runner.invoke(app, ["tool", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["tools"][0]["description"].startswith("Use this when")
