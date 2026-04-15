# Semantic Scholar CLI Reference

All commands are run via uvx:

```bash
uvx --from git+https://github.com/FujishigeTemma/semantic-scholar-cli semantic-scholar <command>
```

## Command Selection

Use the narrowest command that matches the task.

| Need | Command |
| --- | --- |
| Find papers by topic or keyword | `semantic-scholar paper search --query ...` |
| Inspect one known paper | `semantic-scholar paper get --paper-id ...` |
| List authors for a known paper | `semantic-scholar paper authors --paper-id ...` |
| Find papers that cite a known paper | `semantic-scholar paper citations --paper-id ...` |
| Find papers referenced by a known paper | `semantic-scholar paper references --paper-id ...` |
| Find authors by name | `semantic-scholar author search --query ...` |
| Inspect one known author | `semantic-scholar author get --author-id ...` |
| Export citation text | `semantic-scholar citation get --paper-id ... --format ...` |

## Identifier Guidance

- Paper ids can be Semantic Scholar `paperId` values or prefixed ids such as `DOI:10.1038/...` and `ARXIV:1706.03762`.
- Author ids should come from `author search` or prior CLI results before calling `author get`.
- If the user gives an ambiguous natural-language paper title, search first instead of guessing.

## Field Strategy

Default fields are intentionally small.

- Keep defaults when ranking search hits or confirming identity.
- Add fields only when the user explicitly needs them.
- Prefer repeated `--field` flags:
  `--field title --field abstract --field authors`
- Avoid large nested expansions unless the task truly needs them.

Useful paper fields:

- `paperId`
- `title`
- `abstract`
- `year`
- `venue`
- `journal`
- `authors`
- `citationCount`
- `referenceCount`
- `fieldsOfStudy`
- `publicationDate`
- `openAccessPdf`

Useful author fields:

- `authorId`
- `name`
- `affiliations`
- `citationCount`
- `hIndex`
- `paperCount`

## Output Shape

All commands return JSON envelopes:

```json
{"ok":true,"data":{},"meta":{"source":"semantic_scholar_graph_api"}}
```

Failure shape:

```json
{"ok":false,"error":{"code":"...","message":"...","details":{}},"meta":{"source":"semantic_scholar_cli"}}
```

The payload is normalized to `snake_case`.

## Common Patterns

Search then inspect:

```bash
semantic-scholar paper search --query "attention is all you need" --field title --field year
semantic-scholar paper get --paper-id "ARXIV:1706.03762"
```

Disambiguate an author before profile lookup:

```bash
semantic-scholar author search --query "ashish vaswani" --field name --field affiliations
semantic-scholar author get --author-id "author-id-here"
```

## Failure Handling

- `invalid_input`: the CLI arguments were invalid.
- `not_found`: Semantic Scholar returned 404.
- `rate_limited`: Semantic Scholar returned 429.
- `upstream_error`: Semantic Scholar returned another error or malformed JSON.
- `network_error`: the request could not reach Semantic Scholar.
- `timeout`: the request exceeded the configured timeout.
