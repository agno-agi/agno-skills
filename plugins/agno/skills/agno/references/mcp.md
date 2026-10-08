# MCP

| Direction | Guide |
| --- | --- |
| Consume server tools | [MCP tools](https://docs.agno.com/tools/mcp/overview.md) |
| Publish AgentOS components/tools | [AgentOS MCP](https://docs.agno.com/agent-os/mcp/mcp.md) |
| Coding-client access to docs | [Coding agents](https://docs.agno.com/coding-agents.md) |
| Connect clients to your runtime | [CLI connect](https://docs.agno.com/cli/connect.md) |

## Client Lifecycle

Keep `MCPTools` open through the full async run/stream and close through the owning lifespan. Use one instance per server. Prefix colliding names and expose only needed functions.

For [dynamic headers](https://docs.agno.com/tools/mcp/dynamic-headers.md), discovery has no run context and callback errors may leave static headers. Enforce server-side authentication; never share user tokens globally or persist them in run metadata.

Treat stdio packages as executable dependencies. Use the server's timeouts and transport requirements.

## Serving and Identity

`MCPConfig(tools=[...])` defaults to no built-in/lifecycle tools; opt in explicitly. `mcp=True` enables built-ins. Server-card visibility is separate from tool authorization.

Follow [OAuth](https://docs.agno.com/examples/agent-os/mcp/oauth-builtin.md) for hosted clients. REST JWT scopes, MCP identity, transport state, and user isolation are separate controls. Client setup is a requested configuration change.

Inspect `agno/tools/mcp/` and `agno/os/mcp.py` for omitted discovery/header/lifecycle/replica behavior; follow their OAuth imports when authentication is involved.

## Code Patterns

### Consume One Server

Standalone async client; requires `agno[mcp,openai]`, network access, and model credentials.

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

### Serve Selected AgentOS Tools

Save as `mcp_app.py`; requires `agno[os,mcp,openai,sqlite]`. This local-only server has no configured authentication.

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

### Connect and Verify

Client setup command; use the actual AgentOS base URL. Run only when connecting clients is requested.

```bash
uvx agno connect --url http://localhost:7777
```
