# Agno Skills

Official [Agno](https://github.com/agno-agi/agno) skill for coding agents. Build and debug agents, teams, workflows, and AgentOS services using focused references and current official docs.

Covers structured output, streaming, tools, approvals, RAG, learning, MCP, auth, deployment, and evals. It preserves existing project/provider choices; SDK-only tasks need no signup or deployment.

## Install

### skills.sh

For supported coding agents:

```bash
npx skills add https://github.com/agno-agi/agno-skills --skill agno
```

### Claude Code Plugin

Run inside Claude Code:

```text
/plugin marketplace add agno-agi/agno-skills
/plugin install agno@agno-skills
```

### Manual Install

From this repository, copy the skill into your project:

```bash
mkdir -p .claude/skills
cp -r plugins/agno/skills/agno .claude/skills/agno
```

For a global Claude Code installation, use `~/.claude/skills/agno` instead. Other clients have their own skill directories. Review existing files before replacing them.

## Usage

Example requests:

- "Build an Agno docs assistant using my PostgreSQL database."
- "Require human approval before this agent calls a write tool."
- "Serve my agent over MCP with only the selected tools."

Use `/agno` where the client supports skill commands. Docs MCP is optional; the skill can read the official Markdown docs instead.

## Contents and Compatibility

[`SKILL.md`](plugins/agno/skills/agno/SKILL.md) routes requests to topic files in [`references/`](plugins/agno/skills/agno/references). It loads only the guidance needed for the task.

References target **Agno 3.1.1**. Check the project's pinned version and migration guidance before applying newer APIs. Example model IDs do not guarantee account access.

## Updating

For Claude Code: `/plugin update agno@agno-skills`. For skills.sh: `npx skills update`. For manual installations, review and copy changes from the updated repository.

## Maintainer Checks

These Python tools validate the repository; they are **not part of the installed skill** and do not run during installation.

With Python 3.10+:

```bash
uv venv
uv pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check scripts tests
.venv/bin/ruff format --check scripts tests
```

For optional offline API/example checks against published Agno 3.1.1:

```bash
uv pip install -r requirements-smoke.txt
.venv/bin/python -m unittest discover -s tests -v
```

CI runs both suites. They check metadata, links, syntax, imports, constructor arguments, and model-free workflows—not live model calls, external services, or deployment. API tests skip when Agno is absent. When changing guidance, verify it against the relevant docs and installed APIs.

## Sources

- [Documentation index](https://docs.agno.com/llms.txt)
- [Releases](https://github.com/agno-agi/agno/releases)
- [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook)
