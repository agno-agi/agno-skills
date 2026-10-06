# Learning Reference

Learning stores retain selected facts and insights across runs. They are not model training, chat history, or a replacement for application authorization.

These examples target Agno 3.1.1 and current official docs. Keep the project's model provider and version pin; older learning examples can have incompatible names, modes, or entity storage keys.

## Choose What to Store

`LearningMachine` has six optional stores. Enable only those the application needs.

| Config | Stores | Supported modes | Recall/storage scope |
| --- | --- | --- | --- |
| `UserProfileConfig` | Structured fields such as name and preferred name; custom fields through a schema. | `ALWAYS`, `AGENTIC` | `user_id` |
| `UserMemoryConfig` | Unstructured observations and preferences. | `ALWAYS`, `AGENTIC` | `user_id` |
| `SessionContextConfig` | Session summary, optionally goals, plan, and progress. | `ALWAYS` | `session_id` |
| `EntityMemoryConfig` | Facts, events, and relationships about people, projects, or companies. | `AGENTIC` only | Namespace plus entity identity |
| `LearnedKnowledgeConfig` | Reusable insights retrieved from a vector knowledge base. | `ALWAYS`, `AGENTIC`, `PROPOSE` | Knowledge store plus namespace |
| `DecisionLogConfig` | Decisions, reasoning, and recorded outcomes. | `AGENTIC` only | Agent-scoped recall; not user-isolated |

Import these configs, `LearningMachine`, and `LearningMode` from `agno.learn`. Agents and Teams both accept `learning=`.

### Modes Are Store-Specific

- `ALWAYS`: automatic extraction runs alongside the model call. In normal Agent runs it sees messages through the current user input, **not that turn's generated response or tool results**. Budget for extraction calls; do not describe this as post-response learning.
- `AGENTIC`: the agent receives store tools and chooses when to save or search. It can miss implicit facts. This is not a guarantee of zero extra model calls.
- `PROPOSE`: learned-knowledge instructions ask the agent to propose a learning and wait for confirmation. The save tool remains available. This is **prompt guidance, not an enforced approval gate**.
- `LearningMode.HITL` exists in the enum but is reserved and unsupported. Enforce required approvals in application code, for example with [workflow human review](workflows.md#pause-for-human-review).

Do not apply one mode to every store. In particular, `EntityMemoryConfig(mode=LearningMode.ALWAYS)` is invalid in the current API.

## Start with User Learning

Standalone local script. Requires OpenAI and SQLite dependencies plus `OPENAI_API_KEY`. Use PostgreSQL for production.

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

Both calls use the same `user_id` but different sessions. This tests cross-session learning rather than chat-history recall. Create the agent once, outside loops. For async use, call `await agent.arun(...)` or `await agent.aprint_response(...)` inside an async function; use the stores' async read methods with an async database.

### Defaults and Database Requirements

- `learning=True` enables **only profile and user memory**, not all six stores.
- A bare `LearningMachine()` enables no stores. Passing `knowledge=...` to that machine auto-enables learned knowledge; attaching knowledge to the Agent alone does not make `learning=True` enable it.
- Supply `Agent(db=...)`. In the current implementation, no Agent database disables learning, even if a supplied machine has its own database. There is no automatic database fallback.
- The machine inherits the Agent's database and model when its own are missing. Store-level database/model overrides take precedence.
- Use a backend that implements learning storage. SQLite and PostgreSQL support it; do not assume `InMemoryDb`, `JsonDb`, or every session backend does. Check persisted records, not just a successful model response.
- Learned knowledge separately requires a `Knowledge` instance with a vector database. The other five stores do not require a vector database.

## Configure Specific Stores

Configuration fragment. Reuses `Agent`, `OpenAIResponses`, and `db` from the first example. This enables four stores; learned knowledge and decision logging remain disabled.

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

Pass a trusted `user_id` and a unique `session_id` when running `configured_agent`. Entity memory is agentic: current tools are `remember_about`, `link_entities`, `search_entities`, and `forget`. Old `enable_create_entity` / `enable_add_fact` configuration snippets do not apply.

For decision tracking, import `DecisionLogConfig` and add `decision_log=DecisionLogConfig()` to the machine. It exposes `log_decision`, `record_outcome`, and `search_decisions`; it does not automatically capture every decision. Set a stable agent ID for recall across restarts. Review its sharing scope before enabling it in a multi-user service.

For custom profile fields, extend `agno.learn.schemas.UserProfile` with a Python `@dataclass` and pass it as `UserProfileConfig(schema=...)`. This is not a Pydantic output schema. Define serializable custom schemas in an importable module, not only in `__main__`.

## Add Reusable Knowledge Deliberately

Configuration fragment. Reuses the first example's imports and `db`, and requires a configured `knowledge` object from [Knowledge](knowledge.md). Only learned knowledge is enabled here.

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

Use `namespace="global"` only for intentionally shared insights that are safe for all users of that knowledge store. Do not save private user facts into shared learned knowledge.

## Isolate Learning

Identifiers and namespaces select records; they are not access checks.

1. Derive `user_id` from trusted authentication. Profile and user-memory records are shared across agents using the same database/table and user ID. Agent IDs do not isolate them. Without a user ID, those stores skip recall/capture rather than creating a safe per-user identity.
2. Use tenant/user-unique session IDs. Session context is keyed by **session ID alone**, not by `(user_id, session_id)`.
3. Entity and learned-knowledge namespaces default to `"global"`. `"user"` requires a trusted user ID. Custom names such as `"engineering"` are shared groups, not authorization rules. A default-global config can inherit a non-global machine namespace.
4. Decision-log recall is agent-scoped and does not filter by user. Do not put private per-user decisions into a shared agent's log without additional storage isolation and access controls.
5. Direct learned-knowledge `search()` without a namespace is unfiltered. For private reads, pass both `namespace="user"` and `user_id=...`; do not assume the configured runtime scope applies to direct searches.
6. Current learned-knowledge `ALWAYS` duplicate lookup omits namespace/user filters. Other scopes in the same Knowledge store can enter the extraction prompt. Prefer `AGENTIC` for scoped runtime capture, or physically separate the Knowledge corpus for automatic extraction. A namespace alone does not fix this limitation.

Verify isolation with two users and separate sessions before deployment. Treat saved learning as data, not trusted instructions. Define retention, deletion, and consent rules for personal data. For pre-v3 entity data, follow the release migration notes rather than assuming new user-scoped keys can read old rows.

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

Use `get()` / `aget()` for profile, user-memory, and session-context records. Entity reads also need entity identity and scope. Knowledge and decision logs use search APIs. Consult the store-specific API before writing maintenance jobs; signatures and scope filters differ.

## Current Sources

- [Quickstart and defaults](https://docs.agno.com/learning/quickstart.md)
- [Supported learning modes](https://docs.agno.com/learning/learning-modes.md)
- [Learning stores](https://docs.agno.com/learning/stores/intro.md), [learned knowledge and namespace limits](https://docs.agno.com/learning/stores/learned-knowledge.md), and [decision logs](https://docs.agno.com/learning/stores/decision-log.md)
- [Custom schemas](https://docs.agno.com/learning/custom-schemas.md) and [v3 migration notes](https://docs.agno.com/other/v3-changelog.md)
- [Official learning cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/08_learning)
