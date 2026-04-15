"""Tool metadata shaped for model-friendly command selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A future-proof tool contract for CLI and MCP adapters."""

    name: str
    command: str
    description: str
    read_only: bool
    negative_cases: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="paper_search",
        command="paper search",
        description="Use this when the model needs to search for papers by topic, query text, venue, year, or field of study.",
        read_only=True,
        negative_cases=(
            "Do not use for author lookups.",
            "Do not use when you already know the exact paper identifier.",
        ),
    ),
    ToolSpec(
        name="paper_get",
        command="paper get",
        description="Use this when the model already has a paper identifier and needs metadata, abstract, venue, or open access information.",
        read_only=True,
        negative_cases=(
            "Do not use for free-text search.",
            "Do not use for citation export only.",
        ),
    ),
    ToolSpec(
        name="paper_authors",
        command="paper authors",
        description="Use this when the model needs the author list or author metadata for a known paper.",
        read_only=True,
        negative_cases=(
            "Do not use to search authors by name.",
            "Do not use when paper metadata alone is sufficient.",
        ),
    ),
    ToolSpec(
        name="paper_citations",
        command="paper citations",
        description="Use this when the model needs papers that cite a known paper.",
        read_only=True,
        negative_cases=(
            "Do not use for formatted citation strings.",
            "Do not use when references are needed instead of citing papers.",
        ),
    ),
    ToolSpec(
        name="paper_references",
        command="paper references",
        description="Use this when the model needs papers referenced by a known paper.",
        read_only=True,
        negative_cases=(
            "Do not use for formatted citation strings.",
            "Do not use when citing papers are needed instead of references.",
        ),
    ),
    ToolSpec(
        name="author_search",
        command="author search",
        description="Use this when the model needs to find authors by name and compare candidate matches.",
        read_only=True,
        negative_cases=(
            "Do not use when an exact author identifier is already known.",
            "Do not use for paper search.",
        ),
    ),
    ToolSpec(
        name="author_get",
        command="author get",
        description="Use this when the model already has an author identifier and needs profile-level metadata.",
        read_only=True,
        negative_cases=(
            "Do not use for author name disambiguation.",
            "Do not use for paper metadata.",
        ),
    ),
    ToolSpec(
        name="citation_get",
        command="citation get",
        description="Use this when the model needs a formatted citation string for a known paper identifier.",
        read_only=True,
        negative_cases=(
            "Do not use to inspect citing or referenced papers.",
            "Do not use for full paper metadata when citation text is not needed.",
        ),
    ),
)
