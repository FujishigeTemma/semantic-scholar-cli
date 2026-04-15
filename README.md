# semantic-scholar-cli

`semantic-scholar-cli` is a CLI-first interface to the Semantic Scholar Graph API designed for LLM workflows.
It prioritizes strict inputs, stable JSON envelopes, small default payloads, and read-only command surfaces.

## Features

- JSON output by default
- strict, typed inputs
- explicit defaults and bounded limits
- read-only commands only
- model-facing tool metadata via `semantic-scholar tool list`

## Usage

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar --help
```

## API Key

All commands work without an API key, but obtaining one is recommended.

### Why use an API key?

- **Dedicated rate limit** — Without a key, all unauthenticated users share a global pool of 1,000 req/s. During heavy traffic your requests may be throttled or rejected. With a key you get a guaranteed personal allocation.
- **Required endpoints** — Some Semantic Scholar endpoints are only available to authenticated users.
- **Higher limits on request** — The introductory rate limit is 1 req/s per key. You can request a higher quota from Semantic Scholar for research or production use.
- **Better support** — Semantic Scholar can identify your usage and provide targeted help when issues arise.

### Rate limits

| | Without API Key | With API Key |
|---|---|---|
| Rate limit | 1,000 req/s **shared** across all unauthenticated users | 1 req/s **dedicated** per key (introductory) |
| Throttling | May be throttled during heavy usage periods | Stable, guaranteed allocation |
| Authenticated endpoints | Not available | Available |
| Support | None | Key-holder support |

### Setup

Request an API key at <https://www.semanticscholar.org/product/api#api-key>, then:

```bash
export SEMANTIC_SCHOLAR_API_KEY="your-api-key"
```

Or pass it directly:

```bash
semantic-scholar --api-key "your-api-key" paper search --query "..."
```

## Command surface

```text
semantic-scholar paper search
semantic-scholar paper get
semantic-scholar paper authors
semantic-scholar paper citations
semantic-scholar paper references
semantic-scholar author search
semantic-scholar author get
semantic-scholar citation get
semantic-scholar tool list
```

## Output contract

Every command writes JSON to `stdout`.

Success:

```json
{"ok":true,"data":{},"meta":{"source":"semantic_scholar_graph_api"}}
```

Failure:

```json
{"ok":false,"error":{"code":"not_found","message":"...","details":{}},"meta":{"source":"semantic_scholar_cli"}}
```

Use `--pretty` to indent the JSON for human inspection.

## Examples

Search for recent transformer papers:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar paper search \
  --query "transformer interpretability" \
  --year "2023-" \
  --field title \
  --field year \
  --field authors \
  --field citationCount
```

Get a paper by DOI:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar paper get \
  --paper-id "DOI:10.1038/nature14539"
```

List citing papers:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar paper citations \
  --paper-id "649def34f8be52c8b66281af98ae884c09aef38b" \
  --field title \
  --field year \
  --field authors
```

Export a citation:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar citation get \
  --paper-id "ARXIV:1706.03762" \
  --format bibtex
```

Inspect model-facing tool guidance:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar --pretty tool list
```

## Development

```bash
uv run pytest
```
