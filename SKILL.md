---
name: OctenSearch
description: Real-time web search for AI agents powered by Octen. Fast, fresh, and relevant — search the web, filter by date, and get LLM-ready results in under 80ms. Ideal for research, news monitoring, and any task requiring up-to-date information.
homepage: https://octen.ai
metadata: {"clawdbot":{"emoji":"🔍","requires":{"bins":["python3"],"env":["OCTEN_API_KEY"]},"primaryEnv":"OCTEN_API_KEY"}, "homepage" : "https://octen.ai", "support" : "support@octen.ai" }
---

# Octen Search - Real-time Web Search for AI Agents

Octen Search gives your OpenClaw agent the ability to **search the web in real time**. 
Powered by [Octen](https://octen.ai), a search infrastructure purpose-built for AI agents and LLMs.

## What This Skill Does

- 🔍 **Web search**: Search the live web and get structured, LLM-ready results
- ⚡ **Fast**: Average response time under 80ms
- 🕐 **Fresh**: Minute-level index freshness — always up-to-date
- 📅 **Time filtering**: Filter results by publish date (start/end time)
- 🤖 **LLM-native**: Results formatted and ranked specifically for AI consumption

## Usage

```bash
# Basic web search
python3 {baseDir}/scripts/search.py "your search query"

# Control number of results (1-20, default: 5)
python3 {baseDir}/scripts/search.py "your query" -n 10

# Filter by start date
python3 {baseDir}/scripts/search.py "your query" --start_time "2026-01-01T00:00:00Z"

# Filter by date range
python3 {baseDir}/scripts/search.py "your query" --start_time "2026-01-01T00:00:00Z" --end_time "2026-01-31T23:59:59Z"
```

## Options

- `-n, --count <count>`: Optional. Number of results (min: 1, max: 20, if not provided, default to 5)
- `--start_time <time>`: Optional. Start time for filtering results (ISO 8601 format, e.g., "2026-01-01T00:00:00Z")
- `--end_time <time>`: Optional. End time for filtering results (ISO 8601 format, e.g., "2026-01-31T23:59:59Z"). If start_time and end_time are both provided, end_time must be greater than start_time


## Notes
- Needs `OCTEN_API_KEY` in the environment variables, get it from https://octen.ai, then set it like this: `export OCTEN_API_KEY=your-api-key`
- Use `--start_time` and `--end_time` if you want to filter results by time published. For example, to search for news published in January 2026, you can use `--start_time "2026-01-01T00:00:00Z" --end_time "2026-01-31T23:59:59Z"`.

## Security
- The `OCTEN_API_KEY` environment variable is **only sent to the official Octen API endpoint**: `https://api.octen.ai/search`
- No environment variables are sent to any other endpoints or external services
- The API endpoint is **hardcoded and whitelisted** in the code and cannot be modified at runtime
- The skill uses standard HTTP header authentication (`X-Api-Key`) which is the recommended practice for API authentication
- All network requests are made over HTTPS to ensure encrypted transmission of the API key

