# Tools Reference

Give the agent only the tools needed for the task. Use plain typed Python functions for simple tools, `@tool` for behavior controls, and `Toolkit` for a related group. Keep credentials and authorization in application code, not model-generated arguments.

## A Small Custom Tool

Prerequisites: `agno` and `openai`. The tool below is a local demo, not a live policy service. Agent construction is offline; execution needs `OPENAI_API_KEY` and model access.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool


@tool
def lookup_demo_policy(topic: str) -> str:
    """Look up a fictional support policy by topic.

    Args:
        topic: Policy topic, such as refunds or support.
    """
    policies = {
        "refunds": "Demo policy: refund requests are accepted within 30 days.",
        "support": "Demo policy: support is available Monday through Friday.",
    }
    return policies.get(topic.lower(), "No demo policy is available for that topic.")


agent = Agent(
    model=OpenAIResponses(id="gpt-5.6-luna"),
    tools=[lookup_demo_policy],
    instructions="Use the demo policy tool. Label its answer as a fictional policy.",
    tool_call_limit=3,
)

if __name__ == "__main__":
    agent.print_response("What is the demo refund policy?")
```

Type annotations define tool inputs; docstrings tell the model when to call the tool. Validate inputs and source permissions inside the tool. Return bounded, useful results rather than an entire database or API payload.

## Sync and Async Toolkits

Register paired implementations with the same model-visible name. `run()` uses the sync function; `arun()` uses its registered async variant. Async runs can also use sync tools, but that is not a promise that arbitrary blocking work will be nonblocking. Use async clients for network I/O and test the actual tool path.

This example needs `httpx`. Construction does not access the network. Before calling the tool, configure an authorized service URL whose `/health` endpoint returns text.

```python
import httpx
from agno.tools import Toolkit


class HealthTools(Toolkit):
    def __init__(self, base_url: str):
        self.url = base_url.rstrip("/") + "/health"
        super().__init__(
            name="health_tools",
            tools=[self.get_health],
            async_tools=[(self.aget_health, "get_health")],
        )

    def get_health(self) -> str:
        """Get the configured service's health status."""
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.url)
            response.raise_for_status()
            return response.text[:2000]

    async def aget_health(self) -> str:
        """Get the configured service's health status asynchronously."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.text[:2000]
```

Pass a configured `HealthTools` instance in `Agent(tools=[...])`. A standalone `async def` can also be a tool; run it through `arun()` / `aprint_response()`. Keep resource lifetimes inside the same async context. For MCP connection management, see [MCP](mcp.md).

## Approve before a Tool Runs

`requires_confirmation=True` pauses a run; it does not create an approval UI or grant authorization. Show the actual tool name and arguments to the approver. Confirm or reject each pending requirement, then continue the same run. A continuation can pause again.

This complete console demo uses no real messaging service. Imports and construction need no key; running it needs the same model prerequisites as above.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool


@tool(requires_confirmation=True)
def send_demo_message(recipient: str, text: str) -> str:
    """Simulate sending a message after approval; nothing is actually sent."""
    return f"Demo only: would send to {recipient}: {text}"


agent = Agent(
    model=OpenAIResponses(id="gpt-5.6-luna"),
    tools=[send_demo_message],
)

if __name__ == "__main__":
    response = agent.run("Use send_demo_message to send 'Hello' to demo@example.com.")
    while response.is_paused:
        for requirement in response.active_requirements:
            if not requirement.needs_confirmation:
                raise RuntimeError("This demo only handles confirmation requirements")
            call = requirement.tool_execution
            print(call.tool_name, call.tool_args)
            if input("Approve this call? [y/N] ").strip().lower() == "y":
                requirement.confirm()
            else:
                requirement.reject()
        response = agent.continue_run(run_response=response)
    print(response.content)
```

For async code, use `await agent.arun(...)` and `await agent.acontinue_run(run_response=response)` inside an async function. Replace blocking console input with your application's approval channel. To resume by `run_id` after a restart, configure a persistent `db`, retain the `session_id`, and authorize access to the stored run and requirements.

Other pause modes are `requires_user_input=True` with `user_input_fields`, or `external_execution=True` for execution outside Agno. A tool can select only one of these modes or confirmation. See [human confirmation](https://docs.agno.com/hitl/user-confirmation.md) and the [HITL guide](https://docs.agno.com/hitl/overview.md).

## Hooks and Controls

- `@tool(pre_hook=..., post_hook=...)` callbacks receive a `FunctionCall` (from `agno.tools`). Read `fc.function.name`, `fc.arguments`, and `fc.result`; the old `(name, args, result)` lambdas are not the correct signature.
- `tool_hooks` are wrapping middleware. A sync hook receives `function_name`, `function_call`, and `arguments`, calls `function_call(**arguments)`, and returns its result. Match the async hook contract on async paths. Ordinary pre/post-hook exceptions are logged and do not reliably block execution; they are not an authorization gate. See [tool hooks](https://docs.agno.com/tools/hooks.md).
- `include_tools` / `exclude_tools` select Toolkit functions. `requires_confirmation_tools` marks selected Toolkit operations for review. These controls do not replace source permissions.
- `cache_results=True` and `cache_ttl` can help repeatable reads. Do not cache side effects or mix users' sensitive results in a shared cache.
- `stop_after_tool_call=True` ends the run after that tool. Use it deliberately; it can prevent the model from writing a final synthesis.

## Choose an Integration

Use the [toolkit index](https://docs.agno.com/tools/toolkits/overview.md) for current setup, packages, credentials, and available function names. Do not assume installing Agno installs every toolkit dependency.

| Need | Current integration | Prerequisites/caution |
| --- | --- | --- |
| Web search | `WebSearchTools` from `agno.tools.websearch` | `ddgs`, network access; results are untrusted external content |
| Yahoo Finance data | `YFinanceTools` from `agno.tools.yfinance` | `yfinance`, network access; not a source of guaranteed live prices |
| SQL queries | `SQLTools` from `agno.tools.sql` | SQLAlchemy, database driver, authorized database URL; use least-privilege credentials |
| Host file access | `FileTools` from `agno.tools.file` | Restrict file access; do not expose secrets or broad write permissions |
| External MCP tools | `MCPTools` from `agno.tools.mcp` | See [MCP](mcp.md) for async lifecycle and server prerequisites |

For many operations over one source, consider [Context Providers](https://docs.agno.com/context-providers/using-providers.md) rather than exposing every low-level tool. For model-generated code, use a configured isolated execution service such as [Daytona](https://docs.agno.com/tools/toolkits/others/daytona.md) or [E2B](https://docs.agno.com/tools/toolkits/others/e2b.md). These need their own packages, credentials, network policy, and cleanup. Host `ShellTools` or `PythonTools` are not a sandbox.

Keep user-specific state and clients scoped correctly when reusing toolkits. Build agents outside loops, and do not share mutable credentials across users. Consult the [custom toolkit guide](https://docs.agno.com/tools/creating-tools/toolkits.md) for more complex integrations.
