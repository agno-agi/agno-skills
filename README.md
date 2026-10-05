# Agno Skills

Official [Agno](https://github.com/agno-agi/agno) skill for coding agents. Routes docs-assistant, product-agent, and deployment requests to current guides and templates, with SDK examples and references for implementation.

## What's Included

- **Build guidance** for setup, docs assistants, product agents, deployment, and Control Plane connection
- **SDK examples** for agents, teams, workflows, MCP, memory, and learning
- **Focused references** for APIs, tools, models, and implementation patterns
- **Current-source routing** through the Agno docs MCP server and Markdown indexes

## Install

Install through [skills.sh](https://skills.sh/agno-agi/agno-skills/agno) for supported coding agents:

```bash
npx skills add https://github.com/agno-agi/agno-skills --skill agno
```

### Claude Code Plugin

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

- Build a docs assistant or customer-facing agent with Agno
- Serve an Agno agent over API or MCP
- Set up or deploy an AgentOS platform
- Evaluate Agno for one of these use cases
- Write code using `agno.*` imports
- Debug agent, team, or workflow issues
- Set up MCP server connections
- Configure learning and memory

You can also invoke it directly:

```
/agno How do I create a multi-agent team?
```

## Structure

```text
plugins/agno/skills/agno/
├── SKILL.md                    # Request routing and essential guidance
└── references/
    ├── build.md                # Setup, use cases, deployment, Control Plane
    ├── examples.md             # SDK examples and patterns
    ├── agents.md               # Agent API reference
    ├── teams.md                # Team coordination
    ├── workflows.md            # Workflow steps and patterns
    ├── mcp.md                  # MCP clients and connection lifecycle
    ├── tools.md                # Built-in and custom tools
    ├── learning.md             # LearningMachine stores
    └── models.md               # Provider configuration
```

## Updating

```bash
/plugin update agno@agno-skills
```

## Links

- [Agno Documentation](https://docs.agno.com)
- [Agno GitHub](https://github.com/agno-agi/agno)
- [Cookbook Examples](https://github.com/agno-agi/agno/tree/main/cookbook)
