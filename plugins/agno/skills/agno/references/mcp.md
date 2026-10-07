# MCP: Consume Tools or Serve AgentOS

Choose the direction:

| Goal | API |
| --- | --- |
| Let an Agno agent call an external MCP server | `agno.tools.mcp.MCPTools` |
| Expose agents, teams, workflows, or custom tools to MCP clients | `AgentOS(mcp=...)` and `MCPConfig` |
| Give a coding client Agno docs | Connect it to `https://mcp.agno.com` |

See [MCP tools](https://docs.agno.com/tools/mcp/overview.md) and [MCP serving](https://docs.agno.com/features/mcp-server.md). Install `agno[mcp,openai]` for the client; add `os,sqlite` for the server.

## Consume One Server

Set `OPENAI_API_KEY` and confirm model access before running:

```python
import asyncio

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.mcp import MCPTools

async def main():
    async with MCPTools(
        url="https://mcp.agno.com",
        transport="streamable-http",
        timeout_seconds=30,
    ) as docs_tools:
        agent = Agent(
            model=OpenAIResponses(id="gpt-6.1-sol"),
            tools=[docs_tools],
        )
        await agent.aprint_response("How do Agno workflows work?", stream=True)

if __name__ == "__main__":
    asyncio.run(main())
```

Use `transport="stdio"` with `command=` for local subprocesses, or `transport="streamable-http"` with `url=` for HTTP. `sse` is legacy. Review and pin subprocess packages; they run with local permissions. Pass only required environment variables.

## Multiple Servers and Lifecycle

Use **one MCPTools per server**, nested async context managers or `AsyncExitStack`, and `Agent(tools=[...])`. Prefix colliding names with `tool_name_prefix`. Agno 3.1.1 does not export `MultiMCPTools`.

- Keep connections open through the full async run/stream, then close them on completion, error, or cancellation.
- Restrict tools with `include_tools` / `exclude_tools`; filtering is not authorization.
- Use `headers` for fixed credentials or [`header_provider`](https://docs.agno.com/tools/mcp/dynamic-headers.md) for per-run credentials. Discovery has no run context. Callback errors can retain static headers; they do not deny access. Enforce auth server-side. Never share one user’s token globally or persist it in run metadata.
- `refresh_connection` defaults to `False`; `True` refreshes schemas and reconnects only unhealthy sessions. Set server-appropriate timeouts.
- In [AgentOS](https://docs.agno.com/agent-os/mcp/tools.md), let its lifespan manage connections and use `reload=False`. Do not close module-level tools before requests arrive.

## Serve Selected AgentOS Tools

Save as `mcp_app.py`. This local starter configures no authentication; add it before exposure:

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.os import AgentOS, MCPConfig

db = SqliteDb(db_file="tmp/mcp.db")
assistant = Agent(
    id="assistant",
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=db,
)
agent_os = AgentOS(
    agents=[assistant],
    db=db,
    mcp=MCPConfig(
        tools=[assistant.as_tool(name="ask_assistant", description="Ask the assistant")],
        lifecycle_tools=True,
    ),
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="mcp_app:app", host="127.0.0.1", port=7777, reload=False)
```

- The endpoint defaults to `/mcp`. `mcp=True` exposes all eight built-ins. `MCPConfig(tools=[...])` exposes only listed tools: `default_tools` and `lifecycle_tools` default to `False`. This example opts into continue/cancel tools.
- Server cards publish tool names/schemas publicly by default. Set `server_card=False` to disable them.
- For replicas, follow [transport and shared-state configuration](https://docs.agno.com/agent-os/mcp/mcp.md).

## Connect and Verify

[Agno Connect](https://docs.agno.com/cli/connect.md) configures local coding clients:

```bash
uvx agno connect --url http://localhost:7777
```

Pass the **base URL**, not `/mcp`. This changes detected client configuration; run only when requested.

Hosted ChatGPT/Claude connectors require public HTTPS and OAuth for authenticated access, not arbitrary bearer headers. Follow [built-in OAuth](https://docs.agno.com/examples/agent-os/mcp/oauth-builtin.md): exact `AGENTOS_URL`, `MCP_CONNECT_SECRET` (16+ characters), and synchronous database persistence. Leave connector client-ID/secret fields empty; enter the connection secret on consent. Check MCP auth and user isolation separately from REST JWT scopes.

Verify tool discovery, a representative call, and denied unauthorized access. Offline checks cannot establish external MCP/provider interoperability.
