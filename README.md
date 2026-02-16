# Agno Skills

Official [Agno](https://github.com/agno-agi/agno) skills for Claude Code. Provides comprehensive knowledge of the Agno framework for building production-ready agents, teams, workflows, and MCP integrations.

## What's Included

- **Accurate code examples** pulled from the official cookbook
- **API reference** for Agent, Team, Workflow, MCP, Tools, Learning, and Models
- **Best practices** and common patterns
- **120+ built-in tools** reference
- **40+ model providers** reference

## Install

```bash
# Add the marketplace
/plugin marketplace add agno-agi/agno-skills

# Install the Agno skill
/plugin install agno@agno-skills
```

### Manual Install

Copy the skill directly into your project or global config:

```bash
# Project-level
mkdir -p .claude/skills
cp -r plugins/agno/skills/agno .claude/skills/agno

# Global
mkdir -p ~/.claude/skills
cp -r plugins/agno/skills/agno ~/.claude/skills/agno
```

## Usage

Once installed, the skill activates automatically when you:

- Ask about building Agno agents
- Write code using `agno.*` imports
- Debug agent, team, or workflow issues
- Set up MCP server connections
- Configure learning and memory

You can also invoke it directly:

```
/agno How do I create a multi-agent team?
```

## Structure

```
plugins/agno/skills/agno/
├── SKILL.md                    # Main skill (10 examples + patterns)
└── references/
    ├── agents.md               # Agent API reference
    ├── teams.md                # Team modes and coordination
    ├── workflows.md            # Step types (Step, Parallel, Condition, Loop, Router)
    ├── mcp.md                  # MCP integration (stdio, SSE, Streamable HTTP)
    ├── tools.md                # 120+ built-in tools + custom tool creation
    ├── learning.md             # LearningMachine (profiles, memory, entities)
    └── models.md               # 40+ model providers
```

## Updating

```bash
/plugin update agno@agno-skills
```

## Links

- [Agno Documentation](https://docs.agno.com)
- [Agno GitHub](https://github.com/agno-agi/agno)
- [Cookbook Examples](https://github.com/agno-agi/agno/tree/main/cookbook)
