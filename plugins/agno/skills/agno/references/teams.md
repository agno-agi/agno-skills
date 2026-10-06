# Team Reference

Use a team when a model should choose which specialists work on a request. Use a [workflow](workflows.md) when code must control the order or approval gates.

These examples target Agno 3.1.1. Check the project's installed version before copying newer APIs. Examples use `OpenAIResponses`; keep the user's provider and model choice.

## Choose a Mode

Import `Team` and `TeamMode` from `agno.team`.

| Mode | Delegation behavior | Use for |
| --- | --- | --- |
| `TeamMode.coordinate` (default) | Leader selects members, writes tasks, and combines their results. | Work that needs specialist judgment and synthesis. |
| `TeamMode.route` | Leader selects one member and returns its response without synthesis. | A specialist router. |
| `TeamMode.broadcast` | Leader sends the same task to every member, then combines results. | Independent reviews of the same input. |
| `TeamMode.tasks` | Leader creates a shared task list, manages dependencies, and runs an iterative task loop. | Goals that need adaptive decomposition. |

Modes configure the leader's tools; they do not force it to delegate every request. Give clear delegation instructions when members must participate.

- Broadcast members run **sequentially with `run()`**, and concurrently with `arun()`.
- In tasks mode, `max_iterations` bounds the outer task loop. It is not a cap on all model calls or a guarantee that all tasks finish. Inspect task events/state and failures.
- Prefer `mode` to the legacy `respond_directly` and `delegate_to_all_members` flags. Explicit mode takes precedence. Do not use old `collaborate` mode examples.

## Coordinate Two Specialists

Standalone script. Requires the OpenAI and SQLite dependencies and `OPENAI_API_KEY`. SQLite is for this local example; use PostgreSQL for a production service.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.team import Team, TeamMode

writer = Agent(
    id="release-writer",
    name="Writer",
    role="Draft release notes from the supplied facts.",
    model=OpenAIResponses(id="gpt-6.1-sol"),
)
reviewer = Agent(
    id="release-reviewer",
    name="Reviewer",
    role="Find unsupported claims and unclear rollout guidance.",
    model=OpenAIResponses(id="gpt-6.1-sol"),
)
team = Team(
    name="Release Review",
    model=OpenAIResponses(id="gpt-6.1-sol"),
    members=[writer, reviewer],
    mode=TeamMode.coordinate,
    instructions=[
        "Ask Writer for a draft, then ask Reviewer to critique it.",
        "Return revised notes. Do not invent facts missing from the input.",
    ],
    db=SqliteDb(db_file="tmp/release-team.db"),
    markdown=True,
)

if __name__ == "__main__":
    team.print_response(
        "Draft release notes: CSV export is in beta; admins can enable it; "
        "exports are limited to 10,000 rows.",
        user_id="demo-user",
        session_id="release-review-1",
        stream=True,
    )
```

Create members once, not inside a request loop. Explicit member IDs give delegation a stable identity. Members can also be other `Team` instances; give each nested team a clear role.

## Route, Broadcast, or Plan Tasks

Configuration fragments. Reuse `writer`, `reviewer`, and the imports above. Construct the desired mode before running it.

```python
router = Team(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    members=[writer, reviewer],
    mode=TeamMode.route,
    determine_input_for_members=False,  # Pass user-message content unchanged.
    instructions="Route drafting requests to Writer and critiques to Reviewer.",
)

review_team = Team(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    members=[writer, reviewer],
    mode=TeamMode.broadcast,
    instructions="Delegate to both members and combine their recommendations.",
)

task_team = Team(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    members=[writer, reviewer],
    mode=TeamMode.tasks,
    max_iterations=6,
    instructions="Create drafting and review tasks. Make review depend on the draft.",
)
```

Async fragment using `review_team` above. In an existing event loop, call `await main()` instead of `asyncio.run(main())`.

```python
import asyncio


async def main():
    response = await review_team.arun("Review this proposal: make CSV export opt-in.")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
```

`run()` / `arun()` return `TeamRunOutput` without streaming. For formatted output use `print_response()` / `aprint_response()`. With async streaming, iterate `async for event in team.arun(..., stream=True, stream_events=True)`; do not await the iterator. `stream_member_events=True` exposes member events. Tasks mode also emits task-created, task-updated, and iteration events.

## Control Shared Context

Choose each setting for its specific purpose:

- `add_history_to_context=True`: give the leader prior runs from this session. Use `num_history_runs` to bound them.
- `add_team_history_to_members=True`: give members team history; bound it with `num_team_history_runs`.
- `share_member_interactions=True`: share member requests and responses from the current run. This is not persisted history or an ordering guarantee for concurrent members.
- `show_members_responses=True`: display member output. For programmatic retention, use `store_member_responses=True`.
- `output_schema=YourPydanticModel`: constrain the team's final result when typed output is required.

Pass trusted `user_id` and the correct `session_id` per run in multi-user services. Neither a team ID nor a session ID is authorization. Keep mutable member/tool state and stored learning scoped to the caller. See [learning isolation](learning.md#isolate-learning).

## Current Sources

- [Delegation and mode semantics](https://docs.agno.com/teams/delegation.md)
- [Running teams and events](https://docs.agno.com/teams/running-teams.md)
- [Tasks example and iteration limits](https://docs.agno.com/examples/teams/modes/tasks/basic.md)
- [Official team cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/03_teams)
