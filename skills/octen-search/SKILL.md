---
name: octen-search
description: USE FOR broad, multi-angle web search. Powered by Octen — decomposes a question into multiple sub-queries, searches a fresh web index in parallel, and returns ranked results grouped by sub-query (no LLM summary). Best when one query isn't enough — research questions, comparisons, latest-news scans, or wide coverage across many sources.
homepage: https://octen.ai
keywords: [broad search, multi-query search, agentic search, query decomposition, research, web search, octen, RAG, grounding, real-time search, AI search, news]
metadata: {"clawdbot":{"emoji":"🔭","requires":{"bins":["curl"],"env":["OCTEN_API_KEY"]},"primaryEnv":"OCTEN_API_KEY"}, "homepage": "https://octen.ai", "support": "support@octen.ai"}
---

# Octen Broad Search

> **Requires API Key**: Get one at https://octen.ai
>
> Set it: `export OCTEN_API_KEY=your-api-key`

Broad Search is **agentic multi-query search**: it takes a conversation, decomposes the question into multiple sub-queries, and runs them in parallel against Octen's real-time web index. This skill returns the ranked results grouped by sub-query — **no LLM summary** — so the agent reads the raw sources directly.

> This skill always sends `mode: queries_and_search`: you get the decomposed sub-queries and their search results, with no model-generated synthesis.

## API Key Setup

**Before searching, ensure `OCTEN_API_KEY` is set. If it is missing — or any call returns `401` — stop and do not retry blindly: tell the user a key is required, point them to https://octen.ai to get one, help them configure it for their agent (below), then continue once it's set.**

Configure the key for the relevant agent/runtime:

- **Claude Code** — add `{ "env": { "OCTEN_API_KEY": "your-key" } }` to `~/.claude/settings.json` (a transient shell `export` will not persist)
- **Cursor / Hermes / generic shell** — `export OCTEN_API_KEY="your-key"` in `~/.zshrc` or `~/.bashrc`
- **Codex** — `~/.codex/config.toml` → `[shell_environment_policy]`, `set = { OCTEN_API_KEY = "your-key" }`
- **OpenClaw** — add `OCTEN_API_KEY=your-key` to `~/.openclaw/.env`

See the [README](https://github.com/Octen-Team/web-search-skills#prerequisites) for full per-agent instructions.

## When to Use

- **Use `octen-search` (this skill, `/broad-search`)** for questions that benefit from multiple angles: "compare X and Y", "what's the latest on Z", literature/market scans, anything where one search query isn't enough — and you want the underlying sources, not a pre-written summary.
- **Use `octen-web-search` (`/search`)** for a single, direct lookup where you already know the exact query and just want ranked results.

## Sizing the Search

**Set `max_queries` and `count` on every call, scaled to how broad the question is — do not fall back to the API defaults (30 sub-queries × 10 results ≈ 300 pages, slow and token-heavy).** Judge the breadth of the user's question and pick a tier:

| Question breadth | Example | `max_queries` | `count` |
|--|--|--|--|
| **Narrow** — one fact/entity, single angle | "current CEO of Acme", "when did X ship" | 2–3 | 3 |
| **Moderate** — a comparison or "latest on X" | "Postgres vs MySQL for OLTP", "latest on the EU AI Act" | 4–6 | 5 |
| **Broad** — research, survey, many facets | "state of fusion-energy startups", "what's new in AI chips 2026" | 8–12 | 8–10 |

When unsure, use `max_queries: 5` and `count: 5`. Stay within `max_queries` ≤ 30 (the API default ceiling — higher values aren't reliably honored) and `count` ≤ 100 (the enforced max).

## Quick Start (cURL)

### Basic Broad Search (sub-queries + results)
```bash
curl -s -X POST "https://api.octen.ai/broad-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "messages": [
      {"role": "user", "content": "Latest trends in the AI chip market in 2026"}
    ],
    "mode": "queries_and_search",
    "max_queries": 5,
    "web_search_options": {"count": 5}
  }'
```

### Tune Results Per Sub-query
```bash
curl -s -X POST "https://api.octen.ai/broad-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "messages": [{"role": "user", "content": "open-source vector databases comparison"}],
    "mode": "queries_and_search",
    "max_queries": 6,
    "web_search_options": {"count": 5, "highlight": {"enable": true, "max_tokens": 300}}
  }'
```

### With Domain / Time Filtering and Full Content
```bash
curl -s -X POST "https://api.octen.ai/broad-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "messages": [{"role": "user", "content": "recent peer-reviewed findings on GLP-1 drugs"}],
    "mode": "queries_and_search",
    "max_queries": 8,
    "web_search_options": {
      "count": 10,
      "include_domains": ["nature.com", "nih.gov", "thelancet.com"],
      "time_basis": "published",
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2026-01-01T00:00:00Z",
      "highlight": {"enable": true, "max_tokens": 300},
      "full_content": {"enable": true, "max_tokens": 2048}
    }
  }'
```

### Choosing a Decomposition Model
```bash
curl -s -X POST "https://api.octen.ai/broad-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "model": "anthropic/claude-opus-4.8",
    "messages": [{"role": "user", "content": "the state of fusion energy startups"}],
    "mode": "queries_and_search",
    "max_queries": 10,
    "web_search_options": {"count": 8}
  }'
```

## Endpoint

```http
POST https://api.octen.ai/broad-search
```

**Authentication** (either works):
- `X-Api-Key: <API_KEY>` header
- `Authorization: Bearer <API_KEY>` header

**Content-Type**: `application/json`

## Parameters

| Parameter | Type | Required | Default | Description |
|--|--|--|--|--|
| `messages` | object[] | **Yes** | - | The conversation so far. Each item is `{"role": "user"\|"assistant"\|"system", "content": "..."}`. The latest user turn is decomposed into sub-queries. |
| `mode` | string | **Fixed** | `queries_and_search` | Always sent as `queries_and_search` for this skill — returns sub-queries and their search results, no LLM synthesis. |
| `model` | string | No | `anthropic/claude-sonnet-4.6` | Model used for query decomposition (see [Models](#models)) |
| `max_queries` | integer | No | `30` | Target number of sub-queries to generate (recommended 1–30; not strictly enforced server-side) |
| `web_search_options` | object | No | - | Per-search filters applied to every sub-query (see below) |
| `stream` | boolean | No | `false` | Stream incremental chunks instead of one JSON response |

### `web_search_options` Object

| Field | Type | Default | Description |
|--|--|--|--|
| `count` | integer | `10` | Results per sub-query (1–100) |
| `include_domains` | string[] | - | Only include results from these domains (max 1000, each ≤30 chars) |
| `exclude_domains` | string[] | - | Exclude results from these domains (max 150, each ≤30 chars) |
| `include_text` | string[] | - | Strings that must appear in result page text (max 5 items, each ≤30 chars) |
| `exclude_text` | string[] | - | Strings that must not appear in result page text (max 5 items, each ≤30 chars) |
| `time_basis` | string | `auto` | Time field used for filtering: `auto`, `published`, `crawled` |
| `start_time` | string | - | Start time filter, ISO 8601 (e.g. `2025-01-01T00:00:00Z`) |
| `end_time` | string | - | End time filter, ISO 8601 (must be after `start_time`) |
| `highlight` | object | `{"enable": true}` | Highlight options (see below) |
| `format` | string | `text` | Highlight output format: `text` or `markdown` |
| `safesearch` | string | `strict` | Adult content filter: `off` or `strict` |
| `full_content` | object | `{"enable": false}` | Full content options (see below) |

#### `highlight` Options

| Field | Type | Default | Description |
|--|--|--|--|
| `enable` | boolean | `true` | Return query-relevant highlights in each result |
| `max_tokens` | integer | `256` | Max tokens per highlight (100–20000) |

#### `full_content` Options

| Field | Type | Default | Description |
|--|--|--|--|
| `enable` | boolean | `false` | Return full raw page content for each result |
| `max_tokens` | integer | `2048` | Max tokens per result (100–100000) |

### Models

`model` controls query decomposition. Known identifiers below — the server is lenient (an unrecognized value falls back to the default rather than erroring), and this list changes over time, so treat the [API reference](https://docs.octen.ai/api-reference/broad-search) as canonical:

`anthropic/claude-opus-4.8` · `anthropic/claude-opus-4.6` · `anthropic/claude-sonnet-4.6` *(default)* · `anthropic/claude-haiku-4.5` · `google/gemini-3.5-flash` · `google/gemini-3.1-pro-preview` · `google/gemini-3.1-flash-lite` · `google/gemini-3-flash-preview` · `openai/gpt-5.5-pro` · `openai/gpt-5.5` · `openai/gpt-5.4` · `moonshotai/kimi-k2.6` · `moonshotai/kimi-k2.5` · `minimax/minimax-m2.5` · `qwen/qwen3.6-plus`

## Response Format (non-streaming)

A JSON object with the decomposed sub-queries and their grouped search results. No `choices`/synthesis is returned in this mode.

| Field | Type | Description |
|--|--|--|
| `request_id` | string | Unique request identifier |
| `queries[]` | string[] | The decomposed sub-queries |
| `search_results[]` | array | Results grouped per sub-query |
| `search_results[].query` | string | The sub-query these results belong to |
| `search_results[].results[]` | array | Search results (see fields below) |
| `search_results[].latency` | number | Search latency for this sub-query (ms) |
| `meta.latency` | number | Total response time (ms) |

> `meta.usage` (token counts) is only populated when the model synthesizes an answer, so it is not returned in `queries_and_search` mode.

### `search_results[].results[]` Fields

| Field | Type | Description |
|--|--|--|
| `title` | string | Page title |
| `url` | string | Page URL |
| `highlight` | string | Query-relevant snippets (empty unless `highlight.enable` is true) |
| `full_content` | string | Full page content (empty unless `full_content.enable` is true) |
| `authors` | string | Website name or author |
| `time_published` | string | Publish time, ISO 8601 |
| `time_last_crawled` | string | Last crawl time, ISO 8601 |
| `favicon` | string | Favicon URL (empty string when absent) |
| `cover_image` | string \| null | Cover image URL (`null` when absent) |
| `images` | array \| null | Inline images found on the page (`null` when absent) |
| `videos` | array \| null | Inline videos found on the page (`null` when absent) |

### JSON Example

```json
{
  "request_id": "20260615060101592YSCUBFIK7M",
  "queries": [
    "AI chip market trends 2026",
    "latest AI semiconductor trends 2026",
    "AI chip industry outlook 2026"
  ],
  "search_results": [
    {
      "query": "AI chip market trends 2026",
      "results": [
        {
          "title": "Chart: The AI Chip Rush: A Decade of Outsized Growth | Statista",
          "url": "https://www.statista.com/chart/35901/ai-chip-market-global-revenue-forecasts/",
          "highlight": "The global AI semiconductor market is experiencing unprecedented growth ...",
          "full_content": "",
          "authors": "Tristan Gaudiaut",
          "time_published": "2026-02-26T00:00:00Z",
          "time_last_crawled": "2026-04-16T18:52:18Z",
          "favicon": "",
          "cover_image": null,
          "images": null,
          "videos": null
        }
      ],
      "latency": 612
    }
  ],
  "meta": {
    "latency": 1821
  }
}
```

## Streaming (`stream: true`)

Set `"stream": true` to receive incremental chunks. Each chunk carries a `type`:

| `type` | Payload |
|--|--|
| `queries` | The auto-generated sub-queries array (emitted once decomposition finishes) |
| `search_done` | Search results grouped by sub-query (emitted once searches complete) |
| `finish` | Completion signal; `finish_reason` is nested at `choices[0].finish_reason` |

> In `queries_and_search` mode only `queries`, `search_done`, and `finish` are emitted, in that order. The `content` and `usage` chunk types appear only when the model synthesizes (i.e. `full` mode, which this skill does not use).

## Error Codes

All errors return `{ "code": <int>, "msg": "<description>" }` (the body may also include `request_id`).

| HTTP Status | Description |
|--|--|
| `400` | Missing or invalid parameter |
| `401` | Invalid or missing API key |
| `403` | Insufficient balance |
| `429` | Rate limited |
| `500` | Internal server error |

## Security

- API key is sent **only** to the hardcoded endpoint `https://api.octen.ai/broad-search` over HTTPS.
- Authentication uses the standard `X-Api-Key` (or `Authorization: Bearer`) header.
- No environment variables are sent to any other endpoint or external service.

## Notes

- **This skill returns sources, not a summary.** `mode` is fixed to `queries_and_search`; read `search_results` directly and write your own answer from them.
- **Always set `max_queries` and `count`, scaled to the question** — see [Sizing the Search](#sizing-the-search). They trade depth for cost/latency, and the API defaults (30 × 10) are wasteful, so don't rely on them.
- **`web_search_options` applies to every sub-query** — use `include_domains` / `time_basis` + `start_time`/`end_time` to keep all branches scoped to trusted, recent sources.
- **Highlight** is enabled by default; **full content** is off by default — enable `full_content` to pull raw page text for grounding/RAG.
- `messages` accepts multi-turn context, so you can follow up within the same conversation to refine the search.
