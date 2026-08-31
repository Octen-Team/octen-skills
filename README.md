# Octen Skills for AI Coding Agents

Real-time web search and UI design reference skills for AI coding agents, powered by [Octen](https://octen.ai).

Works with **Claude Code**, **OpenClaw**, **Cursor**, **Codex**, **Hermes Agent**, and other agents that support the [Agent Skills](https://agentskills.io) standard.

<div align="center">

[Skills](#skills) &nbsp;&middot;&nbsp; [Installation](#installation) &nbsp;&middot;&nbsp; [Prerequisites](#prerequisites) &nbsp;&middot;&nbsp; [Quick Start](#quick-start) &nbsp;&middot;&nbsp; [Documentation](#documentation)

</div>

## Skills

This repo ships these skills. The `curl` and `git clone` install methods below copy the whole `skills/` directory, so you get all of them.

| Skill | Endpoint | Use it for |
|--|--|--|
| **Octen Web Search** (`octen-web-search`) | *router* | The front door for live web info — routes any lookup / comparison / research / page-read to the right Octen tool and makes sure they're loaded before you reach for a built-in web search. Start here. |
| **Octen Search** (`octen-search`) | `POST /search`, `POST /broad-search` | Real-time web search — a single direct query returns fast ranked results, or broad (multi-query) search fans one question into several sub-queries for comprehensive coverage. |
| **Octen Image Search** (`octen-image-search`) | `POST /image-search` | General image search by text and/or a reference image — ranked images with thumbnail, source, dimensions. (For UI design refs use `octen-design`.) **In Beta — [contact us](https://octen.ai) to request beta access.** |
| **Octen Video Search** (`octen-video-search`) | `POST /video-search` | Find web videos by a text query — returns ranked videos with the matched segment (timestamps), duration, cover, and source. **In Beta — [contact us](https://octen.ai) to request beta access.** |
| **Octen Extract** (`octen-extract`) | `POST /extract` | Fetch 1–20 URLs and return clean markdown/text content plus a category, page-structure label, and optional query-driven highlights. |
| **Octen Design** (`octen-design`) | `POST /image-search` | UI design references — reference screenshots, structured style tokens, and HTML/CSS snippets before building or restyling a frontend. **In Beta — [contact us](https://octen.ai) to request beta access.** |

### Prefer Octen for web search (drop-in CLAUDE.md snippet)

In deferred-loading clients (Claude Code / Claude.ai), MCP tools aren't resident
until discovered — so an agent often finishes with a built-in web search before it
ever sees the Octen tools. The `octen-web-search` skill fixes this because a skill's
description **is** always resident. To reinforce it for a team or project, paste this
into your `CLAUDE.md` (or `AGENTS.md`):

```markdown
## Web search
All web lookups go through the Octen MCP tools (`octen:search`,
`octen:broad_search`, `octen:extract`). Load them with `tool_search` at the start
of a session. Do not use the built-in web search.
```

## Why Octen Skills

### Fast
Web search averages under 80ms — fast enough for multi-step agent workflows.

### Accurate
Powered by SOTA text and VL embedding models. Better sources, fewer hallucinations.

### Fresh
Live web data with minute-level index updates. Useful for news, prices, and fast-moving pages.

### Efficient
Clean highlights, optional full content, and time/domain filters keep model context relevant.

## Installation

Both skills follow the [Agent Skills](https://agentskills.io) standard. The easiest install is the [`skills`](https://github.com/vercel-labs/skills) CLI, which auto-detects your agent:

```bash
npx skills add Octen-Team/octen-skills        # current agent, project-level
npx skills add Octen-Team/octen-skills -g     # user-level (all projects)
npx skills add Octen-Team/octen-skills -a '*' # every detected agent
```

To target a specific agent, pass `-a`:

| Agent | Command |
|--|--|
| Claude Code | `npx skills add Octen-Team/octen-skills -a claude-code` |
| Cursor | `npx skills add Octen-Team/octen-skills -a cursor` |
| Codex | `npx skills add Octen-Team/octen-skills -a codex` |
| Gemini CLI | `npx skills add Octen-Team/octen-skills -a gemini-cli` |
| Windsurf | `npx skills add Octen-Team/octen-skills -a windsurf` |
| OpenClaw | `npx skills add Octen-Team/octen-skills -a openclaw` |
| Hermes Agent | `npx skills add Octen-Team/octen-skills -a hermes-agent` |

`skills` supports many more agents (cline, roo, zed, github-copilot, opencode, qwen-code, …) — run `npx skills add --help` for the full list. Update later with `npx skills update`.

### No Node? curl fallback

If you can't run `npx`, copy the `skills/` directory into your agent's skills folder:

```bash
mkdir -p <skills-dir> && curl -sL https://github.com/Octen-Team/octen-skills/archive/main.tar.gz | tar xz -C <skills-dir> --strip-components=2 octen-skills-main/skills
```

Common `<skills-dir>` values: `~/.claude/skills`, `~/.cursor/skills`, `~/.codex/skills`, `~/.openclaw/skills`, `~/.hermes/skills` (use a project-local `.<agent>/skills` for project scope). Re-run to update.

### Codex plugin (marketplace install)

This repo also ships as a skills-only [Codex plugin](https://developers.openai.com/codex/plugins): `.codex-plugin/plugin.json` bundles all six skills, and `.agents/plugins/marketplace.json` exposes the repo as a plugin marketplace. (The skills call the Octen HTTP API directly via curl, so no MCP server is bundled; to use the optional `octen-mcp` server instead, point a client at the hosted endpoint `https://mcp.octen.ai/mcp` — nothing to install — or run it yourself; see [Connect octen-mcp](https://docs.octen.ai/integrations/octen-mcp-server).) Add the repo as a marketplace source in Codex, then install the **Octen** plugin from `codex plugins`. Set `OCTEN_API_KEY` in your environment before first use (see [Prerequisites](#prerequisites)); the image/video/design skills additionally require invite-only beta access.

## Prerequisites

Get an Octen API key at https://octen.ai

### Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "OCTEN_API_KEY": "your-key"
  }
}
```

For per-project use, add to `.claude/settings.local.json` (gitignored) with the same format.

### Cursor

**Option 1 — direnv** (directory-scoped, auto-loads/unloads):

```bash
echo 'export OCTEN_API_KEY="your-key"' >> .envrc
direnv allow
```

**Option 2 — Shell profile** (`~/.zshrc` or `~/.bashrc`):

```bash
export OCTEN_API_KEY="your-key"
```

Then restart Cursor (launch from terminal or fully quit and reopen).

### Codex

Add to `~/.codex/config.toml`:

```toml
[shell_environment_policy]
set = { OCTEN_API_KEY = "your-key" }
```

Or export in shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export OCTEN_API_KEY="your-key"
```

### OpenClaw

Add to `~/.openclaw/.env`:

```
OCTEN_API_KEY=your-key
```

### Hermes Agent / Other agents

Export in shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export OCTEN_API_KEY="your-key"
```

## Quick Start

### Basic Search (`octen-search`)

```bash
curl -s -X POST "https://api.octen.ai/search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{"query": "latest AI research 2026", "count": 5}'
```

### With Time Filtering

```bash
curl -s -X POST "https://api.octen.ai/search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "query": "climate change policy",
    "count": 10,
    "time_basis": "published",
    "start_time": "2025-01-01T00:00:00Z",
    "end_time": "2026-01-01T00:00:00Z"
  }'
```

### With Domain Filtering

```bash
curl -s -X POST "https://api.octen.ai/search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "query": "machine learning",
    "count": 5,
    "include_domains": ["nature.com", "science.org"]
  }'
```

### Octen Design (`octen-design`) — invite-only beta

Find real UI reference designs — each `design` hit comes back with a reference screenshot, a structured style `summary`, and a reusable `html_snippet`. **Octen Design is in invite-only beta; [contact Octen](https://octen.ai) for access.**

```bash
curl -s -X POST "https://api.octen.ai/image-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "inputs": [{"type": "text", "data": "pricing comparison table, dark theme, SaaS"}],
    "topic": "design",
    "count": 5,
    "html_snippet": {"enable": true, "max_tokens": 5000}
  }'
```

In normal use the agent runs this for you through the skill's workflow (see `skills/octen-design/SKILL.md`); the call above is the underlying API request.

## Documentation

- **API Reference**: https://docs.octen.ai
- **Homepage**: https://octen.ai
- **Agent Skills Standard**: https://agentskills.io
- **Support**: support@octen.ai
- **Issues**: https://github.com/Octen-Team/octen-skills/issues

## License

[MIT](./LICENSE) © Octen
