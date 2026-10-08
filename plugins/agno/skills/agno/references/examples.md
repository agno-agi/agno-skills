# SDK Examples and Patterns

Docs: [First agent](https://docs.agno.com/first-agent.md).

Start with the SDK. Add [AgentOS](agentos.md) only when a service is needed.

## Prerequisites

- For a new environment: `uv pip install "agno[openai,sqlite]"`. Otherwise retain dependency pins and [provider/model choices](models.md).
- Execution needs `OPENAI_API_KEY`, network access, and model access. Check the [adapter configuration](models.md); account availability is not guaranteed.

Each Python block is a separate script. Importing constructs an agent offline without a key. Main guards prevent model calls on import.

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

`print_response()` prints to the console. See [Agents](agents.md) for result, async, and streaming APIs.

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

Use `output_schema`, not prompt-only JSON. Native support varies; parsing failures can leave text in `content`. Keep the type check. See [structured output](https://docs.agno.com/input-output/structured-output/agent.md).

## 3. Persist a Conversation

Needs a writable working directory; running creates `agno-demo.db`. Deployed services need shared persistence, usually PostgreSQL.

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

Reuse the session ID within one conversation; start a new ID for another. Services must derive and authorize IDs from the caller, not trust client-selected IDs. History is not cross-session [user memory](learning.md).

## Next Task

- Tools and approvals: [Tools](tools.md); external connections: [MCP](mcp.md).
- Document search: [Knowledge](knowledge.md) and [Build with Agno](build.md).
- Specialists: [Teams](teams.md); explicit control flow: [Workflows](workflows.md).

Find other current guides in the [docs index](https://docs.agno.com/llms.txt).

## More Docs

- [Building agents](https://docs.agno.com/agents/building-agents.md) and [running agents](https://docs.agno.com/agents/running-agents.md)
- [Sessions](https://docs.agno.com/sessions/overview.md)
- [Model providers](https://docs.agno.com/models/providers/model-index.md)
