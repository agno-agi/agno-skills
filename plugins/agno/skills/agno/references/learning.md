# Memory and Learning

Docs: [Learning](https://docs.agno.com/learning/overview.md), [memory](https://docs.agno.com/memory/overview.md).

History continues a conversation; memory recalls user facts; learning captures profiles, context, entities, knowledge, or decisions. These are not model training or access controls.

## Initialization and Capture

- `learning=True` enables profile/user memory; bare `LearningMachine()` enables no stores. Agent learning needs `Agent(db=...)`, even if the machine has a database.
- Inspect `agent.learning_machine`; `agent.learning` may be only `True`, and disabled stores can be `None`.
- Automatic Agent capture sees messages through current user input, not that turn's response/tool results. Use explicit capture for insights discovered during execution.
- `PROPOSE` is prompt guidance, not an approval gate; `LearningMode.HITL` is unsupported. Store modes differ.

Import configs and `LearningMode` from `agno.learn`; pass them to `LearningMachine(...)` through these keywords:

| Keyword / config | Supported modes |
| --- | --- |
| `user_profile=UserProfileConfig(...)` | `ALWAYS`, `AGENTIC` |
| `user_memory=UserMemoryConfig(...)` | `ALWAYS`, `AGENTIC` |
| `session_context=SessionContextConfig(...)` | `ALWAYS` |
| `entity_memory=EntityMemoryConfig(...)` | `AGENTIC` |
| `learned_knowledge=LearnedKnowledgeConfig(...)` | `ALWAYS`, `AGENTIC`, `PROPOSE` |
| `decision_log=DecisionLogConfig(...)` | `AGENTIC` |

## Isolate Learning

Use authenticated identities. Profile/user-memory records are user-scoped across agents; session context uses session ID alone. Entity/knowledge namespaces default to global; decision-log recall is agent-scoped rather than user-scoped.

Inspect `agno/learn/stores/learned_knowledge.py` for private capture/search: direct search without namespace is unfiltered, and automatic duplicate lookup can omit namespace/user filters. Use separate corpora when extraction must never see another user's data. Namespaces are not access controls.

For supported scoped reads, supply `namespace="user", user_id=trusted_user_id`; use `namespace="global"` only for shared insights. Profile/user-memory stores use `get(user_id=...)` / `aget(user_id=...)`; session context uses `get(session_id=...)` / `aget(session_id=...)`.

Read store-specific source under `agno/learn/stores/` and initialization under `agno/agent/_init.py` / `_managers.py` for capture timing/backend support. For scoring, rollouts, and training-data export, use [source gaps](source-gaps.md).

## Code Patterns

### Start with User Learning

Standalone user-learning example; requires `agno[openai,sqlite]` and model credentials.

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

### Configure Specific Stores

Configuration fragment: reuse `Agent`, `OpenAIResponses`, and `db` from the first block.

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

### Add Reusable Knowledge Deliberately

Configuration fragment: also supply `knowledge` from a configured Knowledge instance; see [Knowledge](knowledge.md).

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

### Inspect Stored Data

Read fragment: reuse `configured_agent` and its initialized learning machine.

```python
learning = configured_agent.learning_machine
if learning is not None:
    if learning.user_memory_store is not None:
        print(learning.user_memory_store.get(user_id="demo-alice"))
    if learning.session_context_store is not None:
        print(learning.session_context_store.get(session_id="alice-introduction"))
```

## More Docs

- [Quickstart and defaults](https://docs.agno.com/learning/quickstart.md)
- [Supported learning modes](https://docs.agno.com/learning/learning-modes.md)
- [Learning stores](https://docs.agno.com/learning/stores/intro.md), [learned knowledge and namespace limits](https://docs.agno.com/learning/stores/learned-knowledge.md), and [decision logs](https://docs.agno.com/learning/stores/decision-log.md)
- [Custom schemas](https://docs.agno.com/learning/custom-schemas.md) and [v3 migration notes](https://docs.agno.com/other/v3-changelog.md)
- [Official learning cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/08_learning)
