# Tools Reference

Expose only needed tools: typed functions for simple calls, `@tool` for controls, `Toolkit` for related operations. Keep credentials and authorization outside model-generated arguments.

## A Small Custom Tool

Requires `agno` and `openai`. This fictional local policy tool is offline; model execution needs `OPENAI_API_KEY` and model access.

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
    model=OpenAIResponses(id="gpt-6.1-sol"),
    tools=[lookup_demo_policy],
    instructions="Use the demo policy tool. Label its answer as a fictional policy.",
    tool_call_limit=3,
)

if __name__ == "__main__":
    agent.print_response("What is the demo refund policy?")
```

Type annotations define inputs; docstrings guide tool selection. Validate inputs and source permissions inside tools. Return bounded results.

## Sync and Async Toolkits

Register pairs under the same model-visible name. `run()` uses sync; `arun()` prefers the registered async variant. Sync fallback does not guarantee nonblocking I/O. Use async clients and test the tool path.

Requires `httpx`; construction is offline. Tool calls need an authorized service URL with a text `/health` response.

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

Pass `HealthTools(base_url=...)` in `Agent(tools=[...])`. Standalone `async def` tools also need `arun()` / `aprint_response()`. Keep resources within one async lifecycle; see [MCP](mcp.md).

## Approve before a Tool Runs

`requires_confirmation=True` pauses, but supplies neither approval UI nor authorization. Show actual tool names/arguments; resolve every requirement before continuing. A continuation can pause again.

This console demo sends nothing. Import/construction need no key; execution needs the model prerequisites above.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool


@tool(requires_confirmation=True)
def send_demo_message(recipient: str, text: str) -> str:
    """Simulate sending a message after approval; nothing is actually sent."""
    return f"Demo only: would send to {recipient}: {text}"


agent = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
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

Inside async functions, use `await agent.arun(...)` and `await agent.acontinue_run(run_response=response)`. Replace blocking input with an approval channel. Resuming by `run_id` after restart needs persistent `db`, retained `session_id`, and caller authorization.

Confirmation, `requires_user_input=True` with `user_input_fields`, and `external_execution=True` are mutually exclusive per tool. See [confirmation](https://docs.agno.com/hitl/user-confirmation.md) and [HITL](https://docs.agno.com/hitl/overview.md).

## Hooks and Controls

- `@tool(pre_hook=..., post_hook=...)` injects `fc: FunctionCall` from `agno.tools`. Read `fc.function.name`, `fc.arguments`, and `fc.result`. Ordinary callback exceptions are logged and execution continues; these hooks are not authorization gates.
- Wrapping `tool_hooks` receive `function_name`, `function_call`, and `arguments`; return `function_call(**arguments)` to continue. Async hooks await that call. See [tool hooks](https://docs.agno.com/tools/hooks.md).
- Toolkit `include_tools` / `exclude_tools` select functions; `requires_confirmation_tools` selects approvals. Neither replaces source permissions.
- `cache_results=True` / `cache_ttl` suit repeatable reads, not side effects or shared sensitive user results.
- `stop_after_tool_call=True` stops without a model-written final synthesis.

## Choose an Integration

Check the [toolkit index](https://docs.agno.com/tools/toolkits/overview.md) or [supported Tools](https://github.com/agno-agi/agno/tree/main/cookbook/91_tools) for dependencies, credentials, and function names.

| Need | Current integration | Prerequisites/caution |
| --- | --- | --- |
| Web search | `WebSearchTools` from `agno.tools.websearch` | `ddgs`, network access; results are untrusted external content |
| Yahoo Finance data | `YFinanceTools` from `agno.tools.yfinance` | `yfinance`, network access; not a source of guaranteed live prices |
| SQL queries | `SQLTools` from `agno.tools.sql` | SQLAlchemy, database driver, authorized database URL; use least-privilege credentials |
| Host file access | `FileTools` from `agno.tools.file` | Restrict file access; do not expose secrets or broad write permissions |
| External MCP tools | `MCPTools` from `agno.tools.mcp` | See [MCP](mcp.md) for async lifecycle and server prerequisites |

Use [Context Providers](https://docs.agno.com/context-providers/using-providers.md) to avoid large low-level tool lists. Model-generated code needs configured isolation, such as Daytona or E2B, with credentials, network policy, and cleanup. Host `ShellTools` / `PythonTools` are not sandboxes.

Scope mutable state, clients, and credentials by caller when reusing toolkits. See [custom toolkits](https://docs.agno.com/tools/creating-tools/toolkits.md) for extensions.
