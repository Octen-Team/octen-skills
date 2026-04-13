# Octen Web Search Skill

A plug-and-play **real-time web search skill** for AI agents, powered by [Octen](https://octen.ai).

Give your agent the ability to search the live web and get fresh, LLM-ready results in under 80ms.

## Features

- 🔍 **Web search** — search the live web, results formatted for LLM consumption
- ⚡ **Fast** — average response time under 80ms
- 🕐 **Fresh** — minute-level index freshness
- 📅 **Time filtering** — filter results by publish date (ISO 8601)
- 🔒 **Secure** — API endpoint hardcoded and whitelisted, API key sent only via HTTPS

## Prerequisites

- Python 3 (no third-party dependencies, only stdlib)
- An **Octen API key**

### Get your API key

1. Go to [https://octen.ai](https://octen.ai) and sign up / log in
2. Create an API key in the dashboard
3. Export it as an environment variable:

   ```bash
   export OCTEN_API_KEY=your-api-key
   ```

   To persist it, add the line to `~/.bashrc`, `~/.zshrc`, or your shell profile.

## Quick Start (standalone CLI)

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
cd web-search-skills

# Basic search
python3 skills/octen-web-search/scripts/search.py "latest AI research 2026"

# Limit number of results (1–20, default 5)
python3 skills/octen-web-search/scripts/search.py "your query" -n 10

# Filter by date range (ISO 8601)
python3 skills/octen-web-search/scripts/search.py "your query" \
    --start_time "2026-01-01T00:00:00Z" \
    --end_time "2026-01-31T23:59:59Z"
```

### CLI options

| Option | Description |
| --- | --- |
| `query` | Search query string (positional, required) |
| `-n, --count <n>` | Number of results, 1–20, default 5 |
| `--start_time <iso>` | Earliest publish time, ISO 8601 (e.g. `2026-01-01T00:00:00Z`) |
| `--end_time <iso>` | Latest publish time, must be greater than `start_time` |

## Installation by Platform

Below are the recommended ways to install this skill in popular agent platforms. All of them ultimately point the agent at `skills/octen-web-search/SKILL.md` or run `search.py` directly.

### Claude Code

Claude Code auto-discovers skills placed under `~/.claude/skills/`. You have two options:

**Option 1 — Install via `npx skills` (recommended)**

```bash
npx skills add Octen-Team/web-search-skills
export OCTEN_API_KEY=your-api-key
```

**Option 2 — Manual copy**

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.claude/skills
cp -r web-search-skills/skills/octen-web-search ~/.claude/skills/
export OCTEN_API_KEY=your-api-key
```

Restart Claude Code. You can now ask things like *"search the web for the latest Llama release"* and the agent will invoke this skill.

### OpenClaw

This skill is published on **clawhub**, so OpenClaw can install it directly. You have two options:

**Option 1 — Install from clawhub (recommended)**

```bash
claw skill install octen-search-skill
export OCTEN_API_KEY=your-api-key
```

**Option 2 — Manual copy**

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.openclaw/skills
cp -r web-search-skills/skills/octen-web-search ~/.openclaw/skills/
export OCTEN_API_KEY=your-api-key
```

### Cursor

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p .cursor/skills
cp -r web-search-skills/skills/octen-web-search .cursor/skills/
export OCTEN_API_KEY=your-api-key
```

### Codex (OpenAI Codex CLI)

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.codex/skills
cp -r web-search-skills/skills/octen-web-search ~/.codex/skills/
export OCTEN_API_KEY=your-api-key
```

### Hermes Agent

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.hermes/skills
cp -r web-search-skills/skills/octen-web-search ~/.hermes/skills/
export OCTEN_API_KEY=your-api-key
```

Restart the agent; the skill will be auto-discovered via its `SKILL.md` frontmatter.

## How It Works

The skill calls a single, hardcoded HTTPS endpoint:

```
POST https://api.octen.ai/search
Header: X-Api-Key: $OCTEN_API_KEY
Body:   { "query": "...", "count": N, "start_time": "...", "end_time": "..." }
```

The endpoint is whitelisted in code and cannot be overridden at runtime. The API key is only read from `OCTEN_API_KEY` and is only sent to the Octen endpoint — no other service receives it.

## Security

- API endpoint is **hardcoded** and **whitelisted** in `search.py` — no runtime override
- The API key is sent via the standard `X-Api-Key` header over HTTPS only
- No third-party Python dependencies, reducing supply-chain surface

## Support

- Homepage: [https://octen.ai](https://octen.ai)
- Issues: open a GitHub issue on this repo
- Email: support@octen.ai

## License

[MIT](./LICENSE) © Octen
