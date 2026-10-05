# MCP: Consume Tools or Serve AgentOS

These are different directions:

| Goal | API |
| --- | --- |
| Let an Agno agent call an external MCP server | `agno.tools.mcp.MCPTools` |
| Expose agents, teams, workflows, or custom tools to MCP clients | `AgentOS(mcp=...)` and `MCPConfig` |
| Give a coding agent access to Agno docs | Connect that client's MCP configuration to `https://mcp.agno.com` |

Read [MCP tools](https://docs.agno.com/tools/mcp/overview.md) and [AgentOS MCP serving](https://docs.agno.com/features/mcp-server.md) for the installed version. Install `agno[mcp,openai]` for the client example and add `os,sqlite` for the server example.

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
            model=OpenAIResponses(id="gpt-5.6-luna"),
            tools=[docs_tools],
        )
        await agent.aprint_response("How do Agno workflows work?", stream=True)

if __name__ == "__main__":
    asyncio.run(main())
```

| Transport | Configuration |
| --- | --- |
| Local subprocess | `MCPTools(command="uvx mcp-server-git", transport="stdio")` |
| HTTP server | `MCPTools(url="https://example.com/mcp", transport="streamable-http")` |
| Legacy SSE server | `MCPTools(url="https://example.com/sse", transport="sse")` |

Choose one transport and its matching command/URL. Pin and review executable packages before starting subprocess servers; they run with local permissions. Pass only required environment variables.

## Multiple Servers and Lifecycle

Create **one MCPTools instance per server**. Nest `async with` blocks or use `contextlib.AsyncExitStack` and pass the connected instances in `Agent(tools=[...])`. Give colliding tool names different `tool_name_prefix` values. `MultiMCPTools` is not exported by Agno 3.1.1; do not copy old examples that import it.

- Keep each connection open for the entire agent run or stream. Prefer context managers so exceptions and cancellations close it.
- Use `include_tools` or `exclude_tools` to expose only intended operations. Tool filtering is not server-side authorization.
- Use `headers` for fixed HTTP headers or `header_provider` for fresh request credentials. Handle discovery calls without a run context. A failing callback is not an authorization gate; the server must reject missing/invalid credentials. Never capture one user's token in a globally shared client.
- MCP client connection management is async. Use `arun()` / `aprint_response()` inside the connection's async lifecycle; this does not mean all of Agno is async-only.
- `refresh_connection=True` checks connection health and refreshes tool schemas before runs; it does not force a new connection every time. Set timeouts for the actual server.
- For AgentOS-managed tool connections and shutdown, follow [MCPTools within AgentOS](https://docs.agno.com/agent-os/mcp/tools.md). Let its lifespan manage those connections, use `reload=False`, and do not wrap the module-level app in a context that closes before requests arrive.

For MCP Toolbox for Databases, consult its current integration and optional dependencies. Its toolkit is `agno.tools.mcp_toolbox.MCPToolbox`, not an export of `agno.tools.mcp`.

## Serve Selected AgentOS Tools

Save as `mcp_app.py`. This is local-only and unauthenticated; add auth before exposing it:

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.os import AgentOS, MCPConfig

db = SqliteDb(db_file="tmp/mcp.db")
assistant = Agent(
    id="assistant",
    model=OpenAIResponses(id="gpt-5.6-luna"),
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

- The default endpoint is `/mcp`. `mcp=True` exposes the built-in default tools; use an explicit `MCPConfig` for a smaller surface.
- In 3.1, `MCPConfig(tools=[...])` publishes **only those tools** by default. `default_tools` and `lifecycle_tools` both default to `False`. The example opts into continue/cancel tools; omit them if not needed.
- A server card can disclose tool names/schemas publicly. Set `server_card=False` when discovery is not intended.
- For replicas, configure stateless transport and shared application state as described in [server configuration](https://docs.agno.com/agent-os/mcp/mcp.md).

## Connect and Verify

For local coding clients, [Agno Connect](https://docs.agno.com/cli/connect.md) discovers and configures the connection:

```bash
uvx agno connect --url http://localhost:7777
```

Pass the **AgentOS base URL**, not its `/mcp` suffix. This command changes detected client configuration; run it only when the user asks to connect those clients.

Hosted ChatGPT/Claude connectors need a public HTTPS MCP endpoint and OAuth for authenticated access; their connector UIs do not accept arbitrary bearer headers. Follow the current [built-in OAuth example](https://docs.agno.com/examples/agent-os/mcp/oauth-builtin.md), including the exact public origin and connection secret. Configure MCP auth separately from REST JWT scopes and check user isolation.

Verify the client's tool list, one representative call, and denied access for an unauthorized caller. A reachable HTTP endpoint alone does not prove MCP interoperability or authorization.
