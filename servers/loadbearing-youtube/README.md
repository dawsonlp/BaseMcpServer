# loadbearing_youtube MCP Server

Extract a YouTube transcript from a URL and expose its **load-bearing
components** — the claims, decisions, tradeoffs, comparison verdicts, and
recommendation the video's conclusion actually rests on. Not a generic summary.

This server is a thin adapter over the
[`loadbearing_youtube`](../../../loadbearing_youtube) package (the first in the
`loadbearing_*` family); all pipeline, provider, and analysis logic lives there.

## Tools

| Tool | What it does |
|---|---|
| `analyze_video` | Fetch transcript + expose load-bearing components (structured data + markdown). |
| `get_video_transcript` | Fetch the full transcript only (no LLM), with optional `[mm:ss]` timestamps. |
| `list_analysis_providers` | List LLM providers, which are configured, and their models. |

## Configuration

Copy `config.yaml.example` and set defaults. Ollama is the local, no-API-key
default; OpenAI/Anthropic work if their keys are set in the environment.

```yaml
analysis:
  provider: "ollama"   # ollama | openai | anthropic
  model: ""            # blank = provider default
  languages: "en"
```

Any tool argument (`provider`, `model`, `languages`) overrides the config; if
both are blank the underlying package falls back to its own `LOADBEARING_*`
environment defaults.

## Run

```bash
# stdio (for MCP clients)
loadbearing-youtube-mcp stdio
# or SSE / HTTP
loadbearing-youtube-mcp sse
```

The server's console script is `loadbearing-youtube-mcp` (the plain
`loadbearing-youtube` name belongs to the package's own CLI).

## Tests

```bash
uv run pytest
```

## Note on the dependency (cleanup item)

`loadbearing_youtube` is currently an **unpublished local sibling repo**, so
`pyproject.toml` resolves it via `[tool.uv.sources]` as an editable path
(`../../../loadbearing_youtube`). When that package is published (PyPI or a git
tag), delete the `[tool.uv.sources]` block and let the
`loadbearing-youtube>=0.1.0` dependency resolve normally.
