# Learning Reference

Learning stores retain facts and insights across runs. They are not model training, chat history, or authorization.

Examples target Agno 3.1.1. Keep the project's provider and version pin; older examples may use incompatible APIs.

## Choose What to Store

`LearningMachine` has six optional stores. Enable only what you need.

| Config | Stores | Supported modes | Recall/storage scope |
| --- | --- | --- | --- |
| `UserProfileConfig` | Structured profile fields. | `ALWAYS`, `AGENTIC` | `user_id` |
| `UserMemoryConfig` | Observations and preferences. | `ALWAYS`, `AGENTIC` | `user_id` |
| `SessionContextConfig` | Summary; optional goals, plan, progress. | `ALWAYS` | `session_id` |
| `EntityMemoryConfig` | Entity facts, events, relationships. | `AGENTIC` only | Namespace plus entity identity |
| `LearnedKnowledgeConfig` | Reusable insights in a vector knowledge base. | `ALWAYS`, `AGENTIC`, `PROPOSE` | Knowledge store plus namespace |
| `DecisionLogConfig` | Decisions, reasoning, outcomes. | `AGENTIC` only | Agent-scoped; not user-isolated |

Import these configs, `LearningMachine`, and `LearningMode` from `agno.learn`. Agents and Teams both accept `learning=`.

### Modes Are Store-Specific

- `ALWAYS`: extraction runs alongside the model call. In Agent runs, it sees messages through the current user input, **not that turn's response or tool results**. Budget for extraction calls.
- `AGENTIC`: the agent chooses when to save/search using tools. It can miss facts and make extra model calls.
- `PROPOSE`: learned-knowledge instructions request confirmation, but the save tool stays available. This is **prompt guidance, not an approval gate**.
- `LearningMode.HITL` is reserved and unsupported. Enforce approvals in application code, such as [workflow human review](workflows.md#pause-for-human-review).

Modes are store-specific: `EntityMemoryConfig(mode=LearningMode.ALWAYS)` is invalid.

## Start with User Learning

Local script requiring OpenAI/SQLite and `OPENAI_API_KEY`. Use PostgreSQL for production.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses

# learning=True enables only user profile and user memory, both in ALWAYS mode.
db = SqliteDb(db_file="tmp/learning.db")
agent = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=db,
    learning=True,
    instructions="Use relevant saved preferences, but do not invent missing facts.",
)

if __name__ == "__main__":
    agent.print_response(
        "I'm Alice Chen. Call me Ali. I prefer short answers with Python examples.",
        user_id="demo-alice",
        session_id="alice-introduction",
    )
    agent.print_response(
        "What name and answer style should you use for me?",
        user_id="demo-alice",
        session_id="alice-followup",
    )

    learning = agent.learning_machine
    if learning is not None and learning.user_profile_store is not None:
        print(learning.user_profile_store.get(user_id="demo-alice"))
```

The same `user_id` across different sessions tests learning, not chat-history recall. Reuse the agent outside loops. Async equivalents: `await agent.arun(...)` / `await agent.aprint_response(...)`; pair async databases with async store reads.

### Defaults and Database Requirements

- `learning=True` enables **only profile and user memory**. Bare `LearningMachine()` enables none; `LearningMachine(knowledge=...)` auto-enables learned knowledge.
- Supply `Agent(db=...)`; without it, Agent learning is disabled even if the machine has a database.
- Missing machine database/model settings inherit from the Agent. Store overrides take precedence.
- Use a learning-capable backend, such as SQLite or PostgreSQL. Do not assume every session backend supports learning; verify persisted records.
- Only learned knowledge needs a `Knowledge` instance with a vector database. Agent-level knowledge alone does not enable it with `learning=True`.

## Configure Specific Stores

Fragment using the first example's imports and `db`. Enables four stores, excluding learned knowledge and decision logging.

```python
from agno.learn import (
    EntityMemoryConfig,
    LearningMachine,
    LearningMode,
    SessionContextConfig,
    UserMemoryConfig,
    UserProfileConfig,
)

configured_agent = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=db,
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
        user_memory=UserMemoryConfig(
            mode=LearningMode.AGENTIC,
            enable_clear_memories=False,
        ),
        session_context=SessionContextConfig(enable_planning=True),
        entity_memory=EntityMemoryConfig(namespace="user"),
    ),
)
```

Pass trusted `user_id` and unique `session_id` values. Entity tools are `remember_about`, `link_entities`, `search_entities`, and `forget`; old `enable_create_entity` / `enable_add_fact` configs do not apply.

[Decision logging](https://docs.agno.com/learning/stores/decision-log.md) captures explicit tool-driven records, not every decision. Use a stable agent ID and review sharing scope below.

[Custom profiles](https://docs.agno.com/learning/custom-schemas.md) use dataclass schemas, not Pydantic output schemas; define serializable schemas in an importable module.

## Add Reusable Knowledge Deliberately

Fragment using the first example's imports/`db` and a configured [Knowledge](knowledge.md) object. Enables only learned knowledge.

```python
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode

knowledge_agent = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=db,
    learning=LearningMachine(
        knowledge=knowledge,
        learned_knowledge=LearnedKnowledgeConfig(
            mode=LearningMode.AGENTIC,
            namespace="user",
        ),
    ),
)
```

Use `namespace="global"` only for insights safe for all users, never private user facts.

## Isolate Learning

Identifiers and namespaces select records; they are not access checks.

1. Derive `user_id` from authentication. Profile/user-memory records share the same database/table and user ID across agents; agent IDs do not isolate them. Without `user_id`, recall/capture is skipped.
2. Use tenant/user-unique session IDs. Session context uses **session ID alone**, not `(user_id, session_id)`.
3. Entity/learned-knowledge namespaces default to `"global"`. `"user"` needs a trusted user ID; custom names are shared groups, not authorization. Default-global configs can inherit a non-global machine namespace.
4. Decision-log recall filters by agent, not user. Private decisions need separate storage isolation and access controls.
5. Direct learned-knowledge `search()` without a namespace is unfiltered. Private reads require both `namespace="user"` and `user_id=...`; runtime scope does not apply automatically.
6. Learned-knowledge `ALWAYS` duplicate lookup omits namespace/user filters, exposing other scopes to the extraction prompt. Prefer `AGENTIC` for scoped runtime capture, or physically separate the Knowledge corpus for automatic extraction. A namespace alone does not fix this.

Test isolation with two users and separate sessions. Treat learning as data, not instructions. Define personal-data retention, deletion, and consent rules. Follow migration notes for pre-v3 entity data.

## Inspect Stored Data

Use `agent.learning_machine`, not `agent.learning` (which may just be `True`). The machine and disabled stores can be `None`.

Read fragment using `configured_agent` above:

```python
learning = configured_agent.learning_machine
if learning is not None:
    if learning.user_memory_store is not None:
        print(learning.user_memory_store.get(user_id="demo-alice"))
    if learning.session_context_store is not None:
        print(learning.session_context_store.get(session_id="alice-introduction"))
```

Use `get()` / `aget()` for profile, user-memory, and session-context records. Entity reads need identity and scope; knowledge and decision logs use search APIs. Check store-specific signatures and filters.

## Current Sources

- [Quickstart and defaults](https://docs.agno.com/learning/quickstart.md)
- [Supported learning modes](https://docs.agno.com/learning/learning-modes.md)
- [Learning stores](https://docs.agno.com/learning/stores/intro.md), [learned knowledge and namespace limits](https://docs.agno.com/learning/stores/learned-knowledge.md), and [decision logs](https://docs.agno.com/learning/stores/decision-log.md)
- [Custom schemas](https://docs.agno.com/learning/custom-schemas.md) and [v3 migration notes](https://docs.agno.com/other/v3-changelog.md)
- [Official learning cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/08_learning)
