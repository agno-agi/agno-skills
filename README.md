# Agno Skills

Official [Agno](https://github.com/agno-agi/agno) skill for coding agents. Build and improve agents, teams, workflows, and AgentOS services with focused references and current-source guidance.

## What It Covers

- SDK setup, structured output, async streaming, tools, and human approval
- Team coordination and tasks; workflows, branching, parallel steps, and resume
- Knowledge/RAG, reranking, published docs pages, memory, and learning
- Skills, context providers, guardrails, and durable files
- API and MCP serving, auth, user isolation, background execution, and deployment
- Evals, tracing, scheduling, and Control Plane connection when requested

The main skill stays small and loads topic references only when needed. It preserves the project's provider, database, framework, and deployment choices. A local SDK question does not require signup or deployment.

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

From a clone of this repository, copy the skill into your project or global configuration:

```bash
# Project-level Claude Code skill
mkdir -p .claude/skills
cp -r plugins/agno/skills/agno .claude/skills/agno

# Or global
mkdir -p ~/.claude/skills
cp -r plugins/agno/skills/agno ~/.claude/skills/agno
```

For other clients, use their documented skill directory or the skills.sh installer. Review an existing installation before overwriting it.

## Usage

The skill activates for Agno tasks, including `agno.*` code, docs assistants, teams, workflows, MCP, learning, and AgentOS. Example prompts:

- "Build a docs assistant using my existing PostgreSQL database."
- "Add human approval before this agent calls a write tool."
- "Serve my agent over MCP with only the selected tools."
- "Check user isolation and background-run recovery in this AgentOS app."

You can also invoke `/agno` in clients that support skill slash commands. Agno docs MCP is optional; the skill can use the official Markdown docs index instead.

## Compatibility

References were reviewed against **Agno 3.1.1** and the current official docs. They include 3.1-specific behavior such as opt-in MCP lifecycle tools and published-page sync progress. Inspect the project's pinned version and matching migration guide before applying them to an older app. Model IDs are examples, not guarantees of account access.

## Structure

```text
plugins/agno/skills/agno/
├── SKILL.md                    # Routing, version checks, implementation rules
└── references/
    ├── build.md                # Use cases, setup, deployment, evidence checklist
    ├── examples.md             # Small SDK starting points
    ├── agents.md               # Configuration, streaming, sessions, context
    ├── teams.md                # Coordinate, route, broadcast, tasks
    ├── workflows.md            # Steps, control flow, progress, pause/resume
    ├── knowledge.md            # RAG, reranking, published pages
    ├── tools.md                # Tools, approvals, guardrails, skills, providers
    ├── mcp.md                  # Consume and serve MCP; connection lifecycle
    ├── learning.md             # Memory and learning stores
    ├── agentos.md              # Serving, security, recovery, evals, operations
    └── models.md               # Provider configuration
```

## Updating

For Claude Code plugin installations:

```text
/plugin update agno@agno-skills
```

For skills.sh installations, use `npx skills update`. For manual installs, update your clone and review/copy the changed skill files.

## Validation and Maintenance

Use Python 3.10+ for repository checks:

```bash
uv venv
uv pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check scripts tests
.venv/bin/ruff format --check scripts tests
```

Validation checks skill metadata, plugin versions, local Markdown links, and Python example syntax. To also run the offline API and example smoke tests against published Agno 3.1.1:

```bash
uv pip install -r requirements-smoke.txt
.venv/bin/python -m unittest discover -s tests -v
```

The smoke tests check imports, constructor keywords, service schemas, and model-free workflow/approval behavior. They skip when Agno is not installed. Neither suite calls model providers or proves that a deployment works. CI runs both suites.

When updating references, verify the installed/released Agno version, read the linked guide, check imports and constructor arguments, and add regression checks for errors found. Keep detailed examples in the topic references, not in `SKILL.md`.

## Links

- [Agno Documentation](https://docs.agno.com)
- [Docs Markdown Index](https://docs.agno.com/llms.txt)
- [Agno Releases](https://github.com/agno-agi/agno/releases)
- [Cookbook Examples](https://github.com/agno-agi/agno/tree/main/cookbook)
