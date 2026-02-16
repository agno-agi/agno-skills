# MCP Integration Reference

## Imports

```python
from agno.tools.mcp import MCPTools, MultiMCPTools
```

## Transport Types

| Transport | Use Case | Parameter |
|-----------|----------|-----------|
| stdio | Local CLI tools (npx, uvx) | `command="uvx mcp-server-git"` |
| sse | Server-Sent Events (legacy) | `transport="sse", url="http://..."` |
| streamable-http | Production HTTP servers | `transport="streamable-http", url="http://..."` |

## MCPTools - Single Server

### stdio Transport (default for commands)

```python
import asyncio
from agno.agent import Agent
from agno.tools.mcp import MCPTools

async def run():
    async with MCPTools(command="uvx mcp-server-git") as tools:
        agent = Agent(tools=[tools])
        await agent.aprint_response("What's the project license?", stream=True)

asyncio.run(run())
```

### Streamable HTTP Transport

```python
async def run():
    async with MCPTools(
        transport="streamable-http",
        url="https://docs.agno.com/mcp",
    ) as tools:
        agent = Agent(tools=[tools], markdown=True)
        await agent.aprint_response("What is Agno?", stream=True)

asyncio.run(run())
```

### Manual Connection Lifecycle

```python
async def run():
    tools = MCPTools(command="uvx mcp-server-git")
    await tools.connect()

    try:
        agent = Agent(tools=[tools])
        await agent.aprint_response("query", stream=True)
    finally:
        await tools.close()
```

## MCPTools Constructor

```python
MCPTools(
    command="uvx mcp-server-git",      # stdio command (auto-detects stdio transport)
    url="http://localhost:8000/mcp",   # HTTP/SSE URL
    transport="streamable-http",       # "stdio", "sse", "streamable-http"
    env={"API_KEY": "..."},            # Environment variables for subprocess
    timeout_seconds=10,                # Read timeout
    include_tools=["tool1", "tool2"],  # Only include specific tools
    exclude_tools=["tool3"],           # Exclude specific tools
    tool_name_prefix="myserver",       # Prefix tool names (avoid collisions)
    refresh_connection=False,          # Refresh connection per agent run
    header_provider=lambda: {"Authorization": f"Bearer {get_token()}"},  # Dynamic headers
)
```

## MultiMCPTools - Multiple Servers

Connect to multiple MCP servers simultaneously:

```python
from agno.tools.mcp import MultiMCPTools

async def run():
    tools = MultiMCPTools(
        # stdio servers (commands)
        commands=[
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-brave-search",
        ],
        # HTTP servers (urls)
        urls=["http://localhost:8000/mcp"],
        urls_transports=["streamable-http"],
        # Shared config
        env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
        timeout_seconds=30,
    )
    await tools.connect()

    agent = Agent(tools=[tools], markdown=True)
    await agent.aprint_response("Find listings in Barcelona", stream=True)
    await tools.close()
```

## MultiMCPTools Constructor

```python
MultiMCPTools(
    commands=["cmd1", "cmd2"],         # List of stdio commands
    urls=["http://..."],               # List of HTTP/SSE URLs
    urls_transports=["streamable-http"],  # Transport per URL
    env={"KEY": "value"},              # Shared environment variables
    timeout_seconds=30,                # Read timeout
    include_tools=["tool1"],           # Filter tools
    exclude_tools=["tool2"],
    tool_name_prefix="prefix",
    refresh_connection=False,
)
```

## Tool Filtering

```python
# Only include specific tools
MCPTools(command="...", include_tools=["read_file", "write_file"])

# Exclude tools
MCPTools(command="...", exclude_tools=["delete_file"])

# Prefix tool names to avoid collisions with multiple servers
MCPTools(command="...", tool_name_prefix="git")
# Tools become: git_read_file, git_write_file, etc.
```

## Dynamic Headers (Auth)

```python
MCPTools(
    transport="streamable-http",
    url="https://api.example.com/mcp",
    header_provider=lambda: {
        "Authorization": f"Bearer {get_fresh_token()}"
    },
)
```

## MCPToolbox (Toolbox Servers)

For MCP Toolbox for Databases and similar toolbox servers:

```python
from agno.tools.mcp import MCPToolbox

toolbox = MCPToolbox(
    url="http://localhost:5000",
    toolsets=["my-toolset"],           # Filter by toolset
    transport="streamable-http",
)
```

## Best Practices

1. **Always close connections** - Use `async with` or try/finally
2. **Set reasonable timeouts** - Default is 10s, increase for slow servers
3. **Use tool_name_prefix** with multiple servers to avoid name collisions
4. **MCP is async-only** - All MCP operations require async/await
5. **Use refresh_connection=True** if server state changes between runs
