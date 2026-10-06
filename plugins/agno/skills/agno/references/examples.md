# SDK Examples and Patterns

Use these small examples for SDK-only tasks. Add a service only when needed; see [AgentOS](agentos.md) and [Build with Agno](build.md).

## Prerequisites

- Use the project's virtual environment and inspect its pinned Agno version. For example: `python -c "from importlib.metadata import version; print(version('agno'))"`.
- These examples use the Agno 3.1.1 API. Check the [release notes](https://github.com/agno-agi/agno/releases) before adapting older projects.
- For a new environment, install `uv pip install "agno[openai,sqlite]"`. Keep an existing project's dependency pins.
- Model execution needs `OPENAI_API_KEY`, network access, and access to the selected model. Construction alone does not need a key. The examples use `OpenAIResponses(id="gpt-6.1-sol")`; confirm model availability for your account.
- Retain the user's provider and model when adapting these examples. See [Models](models.md) for adapter and capability checks.

Each Python block is a separate script. Importing it constructs the agent but does not call a model. Reuse agents; do not create them inside request loops.

## 1. Small Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    name="Support Assistant",
    model=OpenAIResponses(id="gpt-6.1-sol"),
    instructions=[
        "Answer the user's question directly.",
        "State when you do not know; do not invent product policies.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    agent.print_response(
        "Explain the difference between a session and a run.", stream=True
    )
```

`print_response()` is a console helper. Use `run()` when application code needs the result, or `arun()` in an async path. See [Agents](agents.md) for return types and streaming.

## 2. Typed Extraction

No search service is needed: the input contains all the facts.

```python
from typing import Literal

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from pydantic import BaseModel, Field


class Ticket(BaseModel):
    category: Literal["billing", "access", "other"]
    summary: str = Field(description="One sentence based only on the supplied text")


agent = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    output_schema=Ticket,
    instructions="Classify the supplied support request. Do not add facts.",
)

if __name__ == "__main__":
    response = agent.run("I was charged twice for my subscription.")
    if not isinstance(response.content, Ticket):
        raise ValueError("The run did not return a valid Ticket")
    print(response.content.model_dump_json())
```

Use `output_schema`, not prompt-only JSON instructions. Native structured output depends on the adapter and model. Parsing failures can leave text in `content`; a type annotation alone does not validate it. See the [structured-output guide](https://docs.agno.com/input-output/structured-output/agent.md).

## 3. Persist a Conversation

This local demo needs a writable working directory. It creates `agno-demo.db` when run. For a deployed service, use the project's shared persistent database, usually PostgreSQL.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses

agent = Agent(
    id="support-demo",
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=SqliteDb(db_file="agno-demo.db"),
    add_history_to_context=True,
    num_history_runs=3,
)

if __name__ == "__main__":
    agent.print_response(
        "I am evaluating the team plan.",
        user_id="demo-user",
        session_id="plan-evaluation",
    )
    agent.print_response(
        "Which plan did I mention?",
        user_id="demo-user",
        session_id="plan-evaluation",
    )
```

Reuse the same session ID for a continuing conversation. Start a new one for a separate conversation. IDs are not authentication: a service must derive and authorize them from the caller, not trust client-selected IDs. History is not cross-session user memory; see [Learning](learning.md).

## Next Task

| Need | Read |
| --- | --- |
| Async execution, streaming events, context, or media | [Agents](agents.md) |
| Custom tools, approvals, or tool filtering | [Tools](tools.md) |
| Search your documents or build a docs assistant | [Knowledge](knowledge.md), then [Build with Agno](build.md) |
| Persistent user profiles and memories | [Learning](learning.md) |
| Multiple specialists | [Teams](teams.md) |
| Explicit steps, branches, loops, or parallel work | [Workflows](workflows.md) |
| External MCP tools and connection cleanup | [MCP](mcp.md) |
| Serve runs over an API | [AgentOS](agentos.md) |

For a new feature, read its current guide through the [docs index](https://docs.agno.com/llms.txt). Do not copy an unrelated cookbook's dependencies or provider choices.
