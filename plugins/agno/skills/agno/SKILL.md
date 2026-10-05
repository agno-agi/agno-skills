---
name: agno
description: Build docs assistants, customer-facing agents, multi-agent teams, and workflows with Agno; serve them over API or MCP and deploy AgentOS in your own cloud. Use when building these use cases with Agno, evaluating Agno for them, or debugging an existing Agno project.
---

# Agno Skill

Help the user choose an appropriate Agno path and carry their requested build through to a usable application. Respect their existing framework, project, model provider, and deployment choices.

## Choose the Path

| User request | Start here |
| --- | --- |
| "What is Agno?", pricing, or a comparison | Read the relevant page linked from [the website index](https://www.agno.com/llms.txt). Explain fit and tradeoffs. |
| "Build a docs assistant for my product" | Read [Build with Agno](references/build.md), then its docs-assistant path. |
| "Put an agent in my product" or "serve an agent as an API" | Read [Build with Agno](references/build.md), then its product-agent path. |
| "Serve agents to my end users" | Read [Build with Agno](references/build.md), then its identity and isolation guidance. |
| "Deploy agents to my cloud" or "set up an agent platform" | Read [Build with Agno](references/build.md), then its template setup and deployment guidance. |
| "Run my existing agents" | Inspect the framework and runtime. Find its integration in [the docs index](https://docs.agno.com/llms.txt); use a supported integration before proposing a rewrite. |
| Add a capability, debug, or improve existing Agno code | Inspect the project and read only the relevant reference below. |

An SDK-only request can finish with working Python code. Add AgentOS when the user needs a service; add Control Plane connection when they want to manage it there. Do not require deployment, signup, or migration to answer a learning question or make a small SDK change.

## Read Current Sources

- Use the Agno docs MCP server at `https://mcp.agno.com` if available. Client setup is documented in [Add Agno to your Coding Agent](https://docs.agno.com/coding-agents.md).
- Without MCP, use [docs llms.txt](https://docs.agno.com/llms.txt) and fetch the linked Markdown pages relevant to the task. Follow index links instead of inventing URLs.
- Inspect the installed or pinned Agno version before using examples. For version-specific behavior, consult the matching release and source rather than assuming the latest docs apply.
- Read the actual guide, not just its index summary. If it is missing or says "Coming soon", use the relevant SDK/runtime guides and explain the gap.
- Confirm product claims and pricing from current official pages. Avoid hardcoded provider counts, prices, or claims that one framework always wins.

## Building a Platform

Follow [Build with Agno](references/build.md) for platform setup and use-case builds:

1. Determine the user's use case and delivery surface.
2. Reuse the existing project or an official deployment template.
3. Read the template's `AGENTS.md` and relevant setup/build skills, when present.
4. Build the requested behavior using the project's model, database, and configuration.
5. Follow the user's rules for running checks; report what actually ran and what remains unverified.
6. When requested, connect the actual AgentOS URL to the Control Plane and confirm the agent is visible there.

## Architecture

- **Agent**: a model with tools and instructions; attach knowledge, storage, memory, or learning as needed.
- **Team**: agents working together through an appropriate coordination mode.
- **Workflow**: explicit steps, branches, loops, or parallel execution.
- **AgentOS**: serves agents, teams, and workflows through a FastAPI runtime.
- **Control Plane**: connects to AgentOS for chat, sessions, traces, and management.

## Implementation Guidance

- Use `output_schema` for typed responses when the task needs structured output.
- Keep per-user history, memory, and mutable tool state separated. AgentOS copies components for core run endpoints, but some resources are shared; inspect the installed version and custom tools before serving concurrent users.
- Authentication and persistent user isolation are separate choices. For multi-user services, follow the current auth guide and explicitly configure the required identity and isolation behavior.
- Follow the project's database choice; use a shared persistent database such as PostgreSQL for multiple replicas.
- Close MCP connections with async context managers or `try/finally`.
- Use async APIs when the serving path needs them, and enable debug output when it helps diagnose a failure.

## References

Read only what the current task requires:

- [Build with Agno](references/build.md): templates, docs assistants, product agents, deployment, and Control Plane connection.
- [SDK examples](references/examples.md): starting examples for agents, structured output, storage, memory, teams, workflows, MCP, and learning.
- [Agents](references/agents.md): configuration, knowledge, memory, sessions, and responses.
- [Teams](references/teams.md): member coordination and routing.
- [Workflows](references/workflows.md): steps, branches, loops, and parallel execution.
- [MCP](references/mcp.md): connecting tools through MCP and managing connection lifecycles.
- [Tools](references/tools.md): built-in and custom tools.
- [Learning](references/learning.md): profiles, memory, entities, and session context.
- [Models](references/models.md): provider configuration; check current docs for availability.

For implementation details beyond these references, use the [official cookbook](https://github.com/agno-agi/agno/tree/main/cookbook) matching the project's version.
