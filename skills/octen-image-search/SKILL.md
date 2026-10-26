---
name: octen-image-search
description: USE FOR finding images on the web by a text query or a reference image (one input per request), powered by Octen. Returns ranked images with thumbnail, source page, dimensions, and description. Use it for general image search (photos, diagrams, products, screenshots).
homepage: https://octen.ai
keywords: [image search, image, octen, find images, reverse image search, visual search, AI search]
metadata: {"clawdbot":{"emoji":"🖼️","requires":{"bins":["curl"],"env":["OCTEN_API_KEY"]},"primaryEnv":"OCTEN_API_KEY"}, "homepage": "https://octen.ai", "support": "support@octen.ai"}
---

# Octen Image Search

Find images on the web by a **text query or a reference image** (the API
accepts exactly one input per request). Each result includes a thumbnail, the
source page, dimensions, and a description.

## API Key Setup

**Before searching, ensure `OCTEN_API_KEY` is set. On `401`, stop and tell the user a key is required (https://octen.ai). On `403`, the key is valid but the request was refused — relay the message verbatim; the usual cause is insufficient account balance.**

Configure the key for the relevant agent (same as other Octen skills):

- **Claude Code** — add `{ "env": { "OCTEN_API_KEY": "your-key" } }` to `~/.claude/settings.json`
- **Cursor / generic shell** — `export OCTEN_API_KEY="your-key"` in `~/.zshrc` or `~/.bashrc`
- **Codex** — `~/.codex/config.toml` → `[shell_environment_policy]`, `set = { OCTEN_API_KEY = "your-key" }`
- **OpenClaw** — add `OCTEN_API_KEY=your-key` to `~/.openclaw/.env`

## Endpoint

```http
POST https://api.octen.ai/image-search
```

**Authentication**: `X-Api-Key: <API_KEY>` header · **Content-Type**: `application/json`

## Quick Start (cURL)

### By text

```bash
curl -s -X POST "https://api.octen.ai/image-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "inputs": [{"type": "text", "data": "red sports car"}],
    "count": 5
  }'
```

### By reference image (URL or base64)

```bash
curl -s -X POST "https://api.octen.ai/image-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "inputs": [{"type": "image", "url": "https://example.com/car.jpg"}],
    "count": 5
  }'
```

`inputs` accepts exactly **one** entry per request — one text query OR one
image, not both (a second input is rejected with 400). For a local image, send
`{"type": "image", "data": "<base64>"}` (≤5MB after base64 encoding; JPEG/PNG/etc.).

## Parameters

| Parameter | Type | Required | Default | Description |
|--|--|--|--|--|
| `inputs` | array | **Yes** | - | Exactly ONE input: `{"type":"text","data":"<query≤500>"}` or `{"type":"image","url":"<url>"}` or `{"type":"image","data":"<base64>"}` |
| `count` | integer | No | `5` | Number of results (1–10) |
| `include_domains` | string[] | No | - | Only include images from these domains |
| `exclude_domains` | string[] | No | - | Exclude images from these domains |
| `safesearch` | string | No | `strict` | Adult content filter: `off` or `strict` |

There are **no time filters** on this endpoint. `time_range`, `start_time` and
`end_time` are silently dropped here — they return `200` with unfiltered
results rather than an error, so a time-scoped image search fails quietly. Use
them on **octen-search** and **octen-video-search**, which do honour them.

## Response Format

| Field | Type | Description |
|--|--|--|
| `request_id` | string | Unique request identifier |
| `data.results[]` | array | List of image results |
| `data.results[].title` | string | Image / page title |
| `data.results[].url` | string | Full-resolution image URL |
| `data.results[].thumbnail` | string? | Thumbnail URL |
| `data.results[].source_page` | string? | Page the image was found on |
| `data.results[].description` | string? | Description / alt text |
| `data.results[].width` | integer? | Image width (px) |
| `data.results[].height` | integer? | Image height (px) |
| `data.results[].time_published` | string? | Publish time, ISO 8601 |
| `data.results[].time_last_crawled` | string? | Last crawl time, ISO 8601 |
| `meta.latency` | number | Response time in milliseconds |
| `meta.warning` | string? | Warning message, if any |

## Error Codes

| HTTP Status | Description |
|--|--|
| `400` | Missing or invalid parameter |
| `401` | Invalid or missing API key |
| `403` | Insufficient balance |
| `413` | Input too large (image > 5MB base64-encoded) |
| `429` | Rate limited |
| `500` | Internal server error |

## Notes

- `count` is capped at 10.
