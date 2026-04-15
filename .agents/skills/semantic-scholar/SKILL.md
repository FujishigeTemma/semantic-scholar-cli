---
name: semantic-scholar
description: Guide use of the `semantic-scholar` CLI (installed via uvx) for read-only Semantic Scholar research workflows. Use when the agent needs to search papers, inspect paper metadata, follow citations or references, look up authors, or export formatted citations. Prefer this skill when a task involves literature discovery, paper disambiguation, author disambiguation, or citation lookup against Semantic Scholar. Do not use it for general web search, non-Semantic-Scholar sources, or repository code tasks unrelated to academic literature.
---

# Semantic Scholar

Install and run via uvx:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar <command>
```

Use `semantic-scholar` as a read-only, JSON-first command surface over the Semantic Scholar Graph API.
Keep outputs machine-readable unless a human explicitly asks for `--pretty`.

## Workflow

1. Pick the narrowest command that answers the question.
2. Start with default fields unless the task clearly needs more detail.
3. Use `paper search` or `author search` to disambiguate names before calling `get`.
4. Prefer `citation get` only when formatted citation text is required.
5. Return the command result directly when the task is data retrieval, or summarize it after inspection when the user asked a question.

## Command Choice

- For command selection and field guidance, read `references/cli-reference.md`.
- For example prompts that should and should not trigger this skill, read `references/golden-prompts.md`.

## Operating Rules

- Pass identifiers exactly as the CLI expects, for example `DOI:...`, `ARXIV:...`, or a Semantic Scholar `paperId`.
- Use repeated `--field` flags instead of constructing comma-separated field strings yourself.
- Avoid deep field expansions like citations-of-citations unless the task explicitly requires them.
- When search results are ambiguous, stop and compare top candidates before using `paper get` or `author get`.
- Treat the CLI as read-only. Do not invent write, save, or account-management flows.

## Quick Start

- Topic search:
  `semantic-scholar paper search --query "retrieval augmented generation"`
- Exact paper lookup:
  `semantic-scholar paper get --paper-id "ARXIV:1706.03762"`
- Citation export:
  `semantic-scholar citation get --paper-id "ARXIV:1706.03762" --format bibtex`

Load the reference files only when needed.
