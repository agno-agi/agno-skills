# Tools

Docs: [Tools](https://docs.agno.com/tools/overview.md).

Keep credentials and authorization outside model-generated arguments. Validate inputs and source permissions inside the tool; return bounded results.

## Sync and Async Toolkits

Register sync/async pairs under the same model-visible name. `arun()` prefers the async variant, but sync fallback need not be nonblocking. Inspect `agno/tools/toolkit.py` / `function.py`; keep connections alive through the run. Toolkit filters select functions, not data access rights.

## Approve before a Tool Runs

Read [HITL](https://docs.agno.com/hitl/overview.md), [confirmation](https://docs.agno.com/hitl/user-confirmation.md), [external execution](https://docs.agno.com/hitl/external-execution.md), and [persisted approvals](https://docs.agno.com/hitl/approval.md).

- Confirmation, user-input, and external-execution modes are distinct and mutually exclusive per tool. Render actual arguments and resolve every active requirement.
- Pauses supply control flow, not approval UI or caller authorization. Persist IDs and authorize continuation.
- `@approval` adds persisted records; ordinary confirmation alone is not that audit workflow. Inspect `agno/approval/decorator.py` / `agno/run/approval.py` when combining them.
- Pre/post-hook exceptions can be logged without preventing execution. Do not enforce access denial through advisory callbacks.

Decorator syntax: `@tool(requires_confirmation=True)`, `@tool(requires_user_input=True, user_input_fields=[...])`, or `@tool(external_execution=True)`; select one pause mode. Async continuation is `await agent.acontinue_run(run_response=response)`.

Other controls: `@tool(pre_hook=..., post_hook=...)` callbacks receive `fc: FunctionCall` from `agno.tools`; inspect `fc.function.name`, `fc.arguments`, and `fc.result`. Wrapping `tool_hooks` call `function_call(**arguments)` (await it for async). Toolkit `include_tools`, `exclude_tools`, and `requires_confirmation_tools` select functions. `cache_results=True, cache_ttl=...` caches reads; `stop_after_tool_call=True` ends without final synthesis.

## Execution and Large Results

Host shell/Python tools are not sandboxes. Select actual isolation for untrusted generated code. For [offloading](https://docs.agno.com/examples/agents/result-offloading/offload-tool-results.md), inspect `agno/offload/setup.py` / `store.py`: supported backends, failed-write envelopes, expiry, and bounded reads matter.

Use [Context Providers](https://docs.agno.com/context-providers/using-providers.md) for coherent data access and [MCP](mcp.md) for tool servers. Read the selected integration's guide for dependencies/credentials.

## Code Patterns

### A Small Custom Tool

Standalone fictional policy example; model execution needs OpenAI credentials.

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

### Sync and Async Toolkits

Requires `httpx`. Pass the toolkit to an Agent; tool calls require an authorized service URL.

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

### Approve before a Tool Runs

Standalone confirmation example; it simulates sending and has no external write effect.

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

## More Docs

- [Creating tools](https://docs.agno.com/tools/creating-tools/overview.md) and [custom toolkits](https://docs.agno.com/tools/creating-tools/toolkits.md)
- [Tool hooks](https://docs.agno.com/tools/hooks.md)
- [Toolkit catalog](https://docs.agno.com/tools/toolkits/overview.md)
- [Official tools cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/91_tools)
