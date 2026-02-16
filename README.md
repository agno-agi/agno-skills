# Agno Skill for Claude Code

Official [Agno](https://github.com/agno-agi/agno) skill for Claude Code. Gives Claude deep knowledge of the Agno AI agent framework for building production-ready agents, teams, workflows, and MCP integrations.

## What This Skill Does

When you're working with Agno in Claude Code, this skill provides:

- **Accurate code examples** pulled from the official cookbook
- **API reference** for Agent, Team, Workflow, MCP, Tools, Learning, and Models
- **Best practices** and common patterns
- **120+ built-in tools** reference
- **40+ model providers** reference

## Install

### Option 1: Add as a marketplace plugin

```bash
# In Claude Code
/plugin marketplace add agno-agi/agno-skill
/plugin install agno@agno-skill
```

### Option 2: Add directly to your project

Copy the `skills/agno/` directory into your project:

```bash
mkdir -p .claude/skills
cp -r skills/agno .claude/skills/agno
```

### Option 3: Add to your global Claude Code config

```bash
mkdir -p ~/.claude/skills
cp -r skills/agno ~/.claude/skills/agno
```

## Usage

Once installed, Claude Code will automatically use this skill when you:

- Ask about building Agno agents
- Write code using `agno.*` imports
- Debug agent, team, or workflow issues
- Set up MCP server connections
- Configure learning and memory

You can also invoke it directly:

```
/agno How do I create a multi-agent team?
```

## What's Included

```
skills/agno/
├── SKILL.md                    # Main skill file (examples + patterns)
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

This skill is versioned alongside the Agno framework. To get the latest version:

```bash
/plugin update agno@agno-skill
```

## Links

- [Agno Documentation](https://docs.agno.com)
- [Agno GitHub](https://github.com/agno-agi/agno)
- [Cookbook Examples](https://github.com/agno-agi/agno/tree/main/cookbook)
