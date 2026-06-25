# Octen Skills for AI Coding Agents

Real-time web search and UI design reference skills for AI coding agents, powered by [Octen](https://octen.ai).

Works with **Claude Code**, **OpenClaw**, **Cursor**, **Codex**, **Hermes Agent**, and other agents that support the [Agent Skills](https://agentskills.io) standard.

<div align="center">

[Skills](#skills) &nbsp;&middot;&nbsp; [Prerequisites](#prerequisites) &nbsp;&middot;&nbsp; [Installation](#installation) &nbsp;&middot;&nbsp; [Quick Start](#quick-start) &nbsp;&middot;&nbsp; [Documentation](#documentation)

</div>

## Skills

This repo ships two skills. The `curl` and `git clone` install methods below copy the whole `skills/` directory, so you get both.

| Skill | Endpoint | Use it for |
|--|--|--|
| **octen-web-search** | `POST /search` | Real-time web search — a single, direct query returns fast ranked results. |
| **octen-ui-design-search** | `POST /image-search` | UI design references — pull reference screenshots, structured style tokens, and HTML/CSS snippets before building or restyling a frontend. |

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

## Installation

All agents below support the [Agent Skills](https://agentskills.io) standard and read SKILL.md files from their skills directory.

### Claude Code

**npx skills** (recommended):

```bash
npx skills add Octen-Team/web-search-skills
```

**curl** (no git needed):

```bash
# User-level (available in all projects)
mkdir -p ~/.claude/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C ~/.claude/skills --strip-components=2 web-search-skills-main/skills

# Project-level
mkdir -p .claude/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C .claude/skills --strip-components=2 web-search-skills-main/skills
```

**Manual** (git clone + cp):

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.claude/skills && cp -r web-search-skills/skills/* ~/.claude/skills/   # user-level (both skills)
mkdir -p .claude/skills && cp -r web-search-skills/skills/* .claude/skills/        # project-level (both skills)
```

### OpenClaw

**clawhub** (recommended):

```bash
claw skill install octen-search-skill
```

**curl:**

```bash
mkdir -p ~/.openclaw/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C ~/.openclaw/skills --strip-components=2 web-search-skills-main/skills
```

**Manual** (git clone + cp):

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.openclaw/skills
cp -r web-search-skills/skills/* ~/.openclaw/skills/
```

### Cursor

**curl:**

```bash
# Project-level
mkdir -p .cursor/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C .cursor/skills --strip-components=2 web-search-skills-main/skills

# User-level
mkdir -p ~/.cursor/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C ~/.cursor/skills --strip-components=2 web-search-skills-main/skills
```

**Manual** (git clone + cp):

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p .cursor/skills && cp -r web-search-skills/skills/* .cursor/skills/      # project-level (both skills)
mkdir -p ~/.cursor/skills && cp -r web-search-skills/skills/* ~/.cursor/skills/   # user-level (both skills)
```

### Codex

**curl:**

```bash
mkdir -p ~/.codex/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C ~/.codex/skills --strip-components=2 web-search-skills-main/skills
```

**Manual** (git clone + cp):

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.codex/skills
cp -r web-search-skills/skills/* ~/.codex/skills/
```

### Hermes Agent

**curl:**

```bash
mkdir -p ~/.hermes/skills && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C ~/.hermes/skills --strip-components=2 web-search-skills-main/skills
```

**Manual** (git clone + cp):

```bash
git clone https://github.com/Octen-Team/web-search-skills.git
mkdir -p ~/.hermes/skills
cp -r web-search-skills/skills/* ~/.hermes/skills/
```

### Other Agents

**curl** (adjust the target directory for your agent):

```bash
mkdir -p <skills-dir> && curl -sL https://github.com/Octen-Team/web-search-skills/archive/main.tar.gz | tar xz -C <skills-dir> --strip-components=2 web-search-skills-main/skills
```

Or copy from a git clone to the agent's skills directory. All agents following the [Agent Skills](https://agentskills.io) standard read SKILL.md files from their skills folder.

### Updating

**curl**: re-run the curl command above to overwrite with the latest version.

**git clone**: pull the latest changes and re-copy:

```bash
cd web-search-skills && git pull
cp -r skills/* ~/.claude/skills/      # Claude Code
cp -r skills/* .cursor/skills/         # Cursor (project-level)
cp -r skills/* ~/.cursor/skills/       # Cursor (user-level)
cp -r skills/* ~/.codex/skills/        # Codex
cp -r skills/* ~/.openclaw/skills/     # OpenClaw
cp -r skills/* ~/.hermes/skills/       # Hermes Agent
```

## Quick Start

### Basic Search (`octen-web-search`)

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

### UI Design Search (`octen-ui-design-search`)

Find real UI reference designs — each `design` hit comes back with a reference screenshot, a structured style `summary`, and a reusable `html_snippet`:

```bash
curl -s -X POST "https://api.octen.ai/image-search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${OCTEN_API_KEY}" \
  -d '{
    "inputs": [{"type": "text", "data": "pricing comparison table, dark theme, SaaS"}],
    "topic": "design",
    "output_modalities": ["image"],
    "count": 5,
    "html_snippet": {"enable": true, "max_tokens": 5000}
  }'
```

In normal use the agent runs this for you through the skill's workflow (see `skills/octen-ui-design-search/SKILL.md`); the call above is the underlying API request.

## Documentation

- **API Reference**: https://docs.octen.ai
- **Homepage**: https://octen.ai
- **Agent Skills Standard**: https://agentskills.io
- **Support**: support@octen.ai
- **Issues**: https://github.com/Octen-Team/web-search-skills/issues

## License

[MIT](./LICENSE) © Octen
