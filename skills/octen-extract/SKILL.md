---
name: octen-extract
description: USE FOR extracting clean, LLM-ready content from one or more web page URLs, powered by Octen. Fetch 1-20 URLs in one call and get markdown/text content plus a page category, page-structure label, and (optionally) query-driven highlights. Use it for reading articles, scraping pages for RAG/grounding, summarization, or fact lookup from known URLs. It can also list the links on a page.
homepage: https://octen.ai
keywords: [extract, scrape, url, web page, content extraction, markdown, RAG, octen, read url, page links]
metadata: {"clawdbot":{"emoji":"📄","requires":{"bins":["curl"],"env":["OCTEN_API_KEY"]},"primaryEnv":"OCTEN_API_KEY"}, "homepage": "https://octen.ai", "support": "support@octen.ai"}
---

# Octen Extract

Turn one or more URLs into clean, LLM-ready content. Beyond the page body, each
result also carries a **category**, a **page-structure** label, and — when you
pass a `query` — **query-relevant highlights** instead of the full page.

> **Requires API Key**: Get one at https://octen.ai · Set it: `export OCTEN_API_KEY=your-api-key`

## API Key Setup

**Before extracting, ensure `OCTEN_API_KEY` is set. On `401`, stop and tell the user a key is required (https://octen.ai), help them configure it, then continue.** Configure the key for the relevant agent (same as other Octen skills):

- **Claude Code** — add `{ "env": { "OCTEN_API_KEY": "your-key" } }` to `~/.claude/settings.json`
- **Cursor / generic shell** — `export OCTEN_API_KEY="your-key"` in `~/.zshrc` or `~/.bashrc`
- **Codex** — `~/.codex/config.toml` → `[shell_environment_policy]`, `set = { OCTEN_API_KEY = "your-key" }`
- **OpenClaw** — add `OCTEN_API_KEY=your-key` to `~/.openclaw/.env`

## Endpoint

```http
POST https://api.octen.ai/extract
```

**Authentication**: `X-Api-Key: <API_KEY>` header · **Content-Type**: `application/json`

## Quick Start (cURL)

### Batch extract (full content)

```bash
curl -s -X POST "https://api.octen.ai/extract" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "urls": ["https://example.com", "https://octen.ai"],
    "format": "markdown"
  }'
```

### Query-driven highlights (instead of full content)

```bash
curl -s -X POST "https://api.octen.ai/extract" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "urls": ["https://en.wikipedia.org/wiki/Python_(programming_language)"],
    "query": "async programming"
  }'
```

### Hard site (advanced mode)

```bash
curl -s -X POST "https://api.octen.ai/extract" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "urls": ["https://www.reddit.com/r/LocalLLaMA/"],
    "mode": "advanced",
    "timeout": 60
  }'
```

### Mixed batch, difficulty unknown (auto mode)

```bash
curl -s -X POST "https://api.octen.ai/extract" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "urls": ["https://example.com", "https://octen.ai", "https://news.ycombinator.com/item?id=1"],
    "mode": "auto",
    "timeout": 60
  }'
```

### Page links (outbound references first)

```bash
curl -s -X POST "https://api.octen.ai/extract" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "urls": ["https://octen.ai"],
    "include_links": {"scope": "prefer_external", "max_links": 50}
  }'
```

## Parameters

| Parameter | Type | Required | Default | Description |
|--|--|--|--|--|
| `urls` | string[] | **Yes** | - | 1–20 URLs to fetch in one batch |
| `mode` | string | No | `standard` (when omitted) | `standard`, `advanced`, or `auto` — see [Choosing a mode](#choosing-a-mode) |
| `query` | string | No | - | When set, each result returns query-relevant `highlights` and OMITS `full_content` (max 500 chars) |
| `max_age_seconds` | integer | No | `86400` | Accept cached results within this age (min 300); older cached versions are re-fetched |
| `format` | string | No | `markdown` | Content format: `markdown` or `text` |
| `timeout` | integer | No | `30` | Per-URL fetch budget in seconds (1–60) |
| `include_images` | boolean | No | `false` | Include image resources found on the page (also returns `cover_image` when the page has one) |
| `include_videos` | boolean | No | `false` | Include video URLs found on the page |
| `include_audio` | boolean | No | `false` | Include audio URLs found on the page |
| `include_links` | object | No | - | Use it to discover a site's pages or follow outbound references. Returns the page's links: `{scope, max_links}`. `scope`: `prefer_internal` (default; same-site links first) or `prefer_external` (other registered domains first); page order is kept within each group. `max_links`: 1–1000 (default 200; out of range → `400`, not clamped). `{}` uses both defaults |

## Choosing a mode

You pick the mode; omitting it means `standard`.

- **`standard`** (default): fastest and cheapest. Right for ordinary, well-structured pages without anti-bot protection — news, blogs, docs, product pages, static sites. On login-walled, JS-heavy, or anti-bot sites it can return empty content or just a page skeleton **while still reporting `status: "success"`**.
- **`advanced`**: highest success rate — renders in a real browser with stronger anti-bot handling; slower and 2.5x the price. Use it for known hard sites: anti-bot/WAF-protected sites, JS-heavy SPAs, social sites (Reddit, X, LinkedIn), academic sites (ResearchGate), dynamically loaded content.
- **`auto`**: decides per URL — standard where it suffices, advanced only for hard URLs; each URL is billed at the mode it actually used. Use it for a mixed batch when you can't tell which URLs are hard. If most URLs are hard, its cost approaches all-advanced.

| Scenario | `mode` |
|--|--|
| News / blogs / docs / product pages (ordinary sites) | `standard` (or omit) |
| Known hard sites (Reddit / X / LinkedIn / ResearchGate / anti-bot / SPA) | `advanced` |
| Mixed batch, unsure which are hard | `auto` |
| Cost-sensitive, mostly ordinary sites | `standard` |
| Quality first, mostly hard sites | `advanced` |

**Rule of thumb**: all ordinary sites → `standard` (or omit); known hard sites → `advanced`; mixed or unsure → `auto`.

**Recovery**: if a `standard` result failed, or came back empty/skeletal (`page_structure.primary` is `"No Main Content"`, or very short content on a page that should have a body), retry just those URLs with `"mode": "advanced"`.

**Timeout**: `advanced` and `auto` are slower — raise `timeout` (e.g. `60`).

## Response Format

| Field | Type | Description |
|--|--|--|
| `request_id` | string | Unique request identifier |
| `data.results[]` | array | One result per URL |
| `data.results[].url` | string | The URL |
| `data.results[].status` | string | `success` or `failed` |
| `data.results[].resolved_mode` | string? | `standard` or `advanced` — the mode actually used for this URL. Present on success, absent on failure. May differ from the requested mode (`auto` picks per URL; `advanced` can resolve to `standard`) |
| `data.results[].error_message` | string? | Why it failed (when `status` = failed) |
| `data.results[].title` | string? | Page title |
| `data.results[].full_content` | string? | Cleaned page content (when no `query`) |
| `data.results[].highlights` | string[]? | Query-relevant snippets (when `query` is set) |
| `data.results[].category` | object? | `{primary, secondary}` — what the page is about |
| `data.results[].page_structure` | object? | `{primary, secondary}` — what kind of page it is |
| `data.results[].time_published` | string? | Publish time, ISO 8601 |
| `data.results[].time_last_crawled` | string? | Last crawl time, ISO 8601 |
| `data.results[].favicon` | string? | Page favicon URL — returned by default when available |
| `data.results[].cover_image` | object? | `{url}` — page cover image (when `include_images` is true and the page has one) |
| `data.results[].images` / `videos` / `audio` | object[]? | `[{url}]` — media found on the page (when the matching `include_*` is true) |
| `data.results[].links` | object[]? | `[{url, anchor_text, is_external}]` — page links (on success, when `include_links` is set and links were found) |
| `meta.usage.total_urls` | integer | URLs requested |
| `meta.usage.successful_urls` | integer | URLs successfully fetched |
| `meta.usage.successful_by_mode` | object | `{standard_urls, advanced_urls}` — successful URLs per mode. **Actual billing is authoritative from these counts**, not from summing `resolved_mode` |
| `meta.warning` | string | e.g. `"1 URL(s) failed and were not billed"`; empty string when there is nothing to report |

`meta` is top-level (a sibling of `data`), not `data.meta`.

## Error Codes

| HTTP Status | Description |
|--|--|
| `400` | Missing or invalid parameter |
| `401` | Invalid or missing API key |
| `403` | Insufficient balance |
| `429` | Rate limited |
| `500` | Internal server error |

## Notes

- **Partial success is first-class**: a failed URL is returned with `status: "failed"` + an `error_message`; sibling URLs in the same batch still succeed. Always check per-result `status`.
- Pass `query` only when you want focused `highlights` for RAG/grounding; omit it to get the full cleaned page.
- **Pricing**: `standard` $1 / 1K successful URLs, `advanced` $2.5 / 1K. Failed URLs are not billed.
- `category` and `page_structure` let you route or filter pages (e.g., skip an index/operation page, keep a content page) without reading the whole body.
