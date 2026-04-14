# Octen Web Search Skill

Real-time web search skill for AI coding agents, powered by [Octen](https://octen.ai).

Works with **Claude Code**, **OpenClaw**, **Cursor**, **Codex**, **Hermes Agent**, and other agents that support the [Agent Skills](https://agentskills.io) standard.

<div align="center">

[Prerequisites](#prerequisites) &nbsp;&middot;&nbsp; [Installation](#installation) &nbsp;&middot;&nbsp; [Quick Start](#quick-start) &nbsp;&middot;&nbsp; [Documentation](#documentation)

</div>

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
mkdir -p ~/.claude/skills && cp -r web-search-skills/skills/octen-web-search ~/.claude/skills/   # user-level
mkdir -p .claude/skills && cp -r web-search-skills/skills/octen-web-search .claude/skills/        # project-level
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
cp -r web-search-skills/skills/octen-web-search ~/.openclaw/skills/
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
mkdir -p .cursor/skills && cp -r web-search-skills/skills/octen-web-search .cursor/skills/      # project-level
mkdir -p ~/.cursor/skills && cp -r web-search-skills/skills/octen-web-search ~/.cursor/skills/   # user-level
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
cp -r web-search-skills/skills/octen-web-search ~/.codex/skills/
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
cp -r web-search-skills/skills/octen-web-search ~/.hermes/skills/
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
cp -r skills/octen-web-search ~/.claude/skills/      # Claude Code
cp -r skills/octen-web-search .cursor/skills/         # Cursor (project-level)
cp -r skills/octen-web-search ~/.cursor/skills/       # Cursor (user-level)
cp -r skills/octen-web-search ~/.codex/skills/        # Codex
cp -r skills/octen-web-search ~/.openclaw/skills/     # OpenClaw
cp -r skills/octen-web-search ~/.hermes/skills/       # Hermes Agent
```

## Quick Start

### Basic Search

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

## Documentation

- **API Reference**: https://docs.octen.ai
- **Homepage**: https://octen.ai
- **Agent Skills Standard**: https://agentskills.io
- **Support**: support@octen.ai
- **Issues**: https://github.com/Octen-Team/web-search-skills/issues

## License

[MIT](./LICENSE) © Octen
