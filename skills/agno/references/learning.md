# Learning Reference

## Overview

The LearningMachine provides persistent learning across sessions with 5 stores:

| Store | Purpose | Data Type |
|-------|---------|-----------|
| User Profile | Structured user fields | Name, preferences, custom fields |
| User Memory | Observations about users | Unstructured text memories |
| Session Context | Current session state | Goal, plan, progress, summary |
| Entity Memory | Third-party entity facts | Facts, events, relationships |
| Learned Knowledge | Reusable insights | Patterns and knowledge across users |

## Imports

```python
from agno.learn import (
    LearningMachine,
    LearningMode,
    UserProfileConfig,
    UserMemoryConfig,
    SessionContextConfig,
    EntityMemoryConfig,
    LearnedKnowledgeConfig,
)
```

## Learning Modes

```python
class LearningMode(Enum):
    ALWAYS = "always"    # Auto-extract after each response (invisible to agent)
    AGENTIC = "agentic"  # Agent decides when to learn via tool calls
    PROPOSE = "propose"  # Agent proposes, human confirms
```

## Basic Setup

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.learn import LearningMachine, LearningMode, UserProfileConfig, UserMemoryConfig

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
    ),
)
```

## Store Configurations

### User Profile

Captures structured profile fields (name, preferred name, custom fields).

```python
UserProfileConfig(
    mode=LearningMode.ALWAYS,          # Auto-extract after each response
    db=db,                             # Override default db
    model=model,                       # Override default model
    schema=CustomProfileSchema,        # Custom Pydantic schema for fields
    enable_update_profile=True,        # Allow profile updates
    instructions="Focus on preferences and work details",
)
```

### User Memory

Stores unstructured observations about users.

```python
UserMemoryConfig(
    mode=LearningMode.AGENTIC,        # Agent decides when to store
    enable_add_memory=True,
    enable_update_memory=True,
    enable_delete_memory=True,
    enable_clear_memories=False,       # Safety: don't allow bulk delete
    instructions="Remember important facts and preferences",
)
```

### Session Context

Tracks current session state (goal, plan, progress).

```python
SessionContextConfig(
    mode=LearningMode.ALWAYS,
    enable_planning=True,              # Track goals and plans
    enable_add_context=True,
    enable_update_context=True,
)
```

### Entity Memory

Facts about third-party entities (people, companies, projects).

```python
EntityMemoryConfig(
    mode=LearningMode.ALWAYS,
    namespace="global",                # Shared across users
    enable_create_entity=True,
    enable_add_fact=True,
    enable_add_event=True,
    enable_add_relationship=True,
)
```

### Learned Knowledge

Reusable patterns and insights across users (requires knowledge base with vector DB).

```python
LearnedKnowledgeConfig(
    mode=LearningMode.AGENTIC,
    knowledge=knowledge_base,          # Vector knowledge base
    namespace="global",
    agent_can_save=True,
    agent_can_search=True,
)
```

## Full Example

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.learn import (
    LearningMachine, LearningMode,
    UserProfileConfig, UserMemoryConfig,
    SessionContextConfig, EntityMemoryConfig,
)
from agno.models.openai import OpenAIResponses

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
        session_context=SessionContextConfig(mode=LearningMode.ALWAYS, enable_planning=True),
        entity_memory=EntityMemoryConfig(mode=LearningMode.ALWAYS),
    ),
    markdown=True,
)

user_id = "alice@example.com"

# Session 1: Agent learns about user
agent.print_response(
    "Hi! I'm Alice Chen, call me Ali. I work at TechCorp as a data scientist.",
    user_id=user_id,
    session_id="session_1",
    stream=True,
)

# Access stored data
agent.learning_machine.user_profile_store.print(user_id=user_id)

# Session 2: Agent recalls everything
agent.print_response(
    "What do you remember about me?",
    user_id=user_id,
    session_id="session_2",
    stream=True,
)
```

## Quick Enable (Defaults)

For simple cases, just pass `learning=True`:

```python
agent = Agent(
    model=model,
    db=db,
    learning=True,  # Enables all stores with defaults
)
```

## Accessing Stores

```python
# Print stored data
agent.learning_machine.user_profile_store.print(user_id=user_id)
agent.learning_machine.user_memory_store.print(user_id=user_id)
agent.learning_machine.session_context_store.print(user_id=user_id, session_id=session_id)
agent.learning_machine.entity_memory_store.print(user_id=user_id)
```
