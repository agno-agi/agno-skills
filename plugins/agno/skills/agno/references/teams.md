# Team Reference

Docs: [Teams](https://docs.agno.com/teams/overview.md).

Use a team for model-led delegation, or a [workflow](workflows.md) for code-controlled order and approval gates.

## Choose a Mode

Import `Team` and `TeamMode` from `agno.team`.

| Mode | Delegation behavior | Use for |
| --- | --- | --- |
| `TeamMode.coordinate` (default) | Leader selects members, writes tasks, and combines results. | Specialist judgment and synthesis. |
| `TeamMode.route` | Leader selects one member and returns its response directly. | Specialist routing. |
| `TeamMode.broadcast` | Leader sends the same task to all members, then combines results. | Independent reviews. |
| `TeamMode.tasks` | Leader manages a shared task list and dependencies iteratively. | Adaptive decomposition. |

Modes do not force delegation. Instruct the leader when members must participate.

- Broadcast runs members **sequentially with `run()`**, concurrently with `arun()`.
- `max_iterations` bounds the tasks-mode outer loop, not model calls or task completion. Inspect task state and failures.

## Coordinate Two Specialists

Standalone script. Requires OpenAI/SQLite dependencies and `OPENAI_API_KEY`. Use PostgreSQL for production.

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

Explicit IDs stabilize delegation identity. Nested `Team` members also need clear roles.

## Route, Broadcast, or Plan Tasks

Configuration fragments using `writer`, `reviewer`, and the imports above.

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

Async fragment using `review_team`. In an existing event loop, use `await main()` instead of `asyncio.run(main())`.

```python
import asyncio


async def main():
    response = await review_team.arun("Review this proposal: make CSV export opt-in.")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
```

`run()` / `arun()` return `TeamRunOutput` without streaming. Format output with `print_response()` / `aprint_response()`. For async streaming, use `async for event in team.arun(..., stream=True, stream_events=True)`, not `await`. Member events are included by default (`stream_member_events=True`).

## Control Shared Context

- `add_history_to_context=True`: leader session history, bounded by `num_history_runs`.
- `add_team_history_to_members=True`: member access to team history, bounded by `num_team_history_runs`.
- `share_member_interactions=True`: share member requests and responses from the current run. This is not persisted history or an ordering guarantee for concurrent members.
- `show_members_responses=True`: display member output. For programmatic retention, use `store_member_responses=True`.
- `output_schema=YourPydanticModel`: typed final output.

Pass trusted `user_id` and `session_id` per run. Scope mutable member/tool state and stored learning to the caller. See [learning isolation](learning.md).

## More Docs

- [Delegation and mode semantics](https://docs.agno.com/teams/delegation.md)
- [Running teams and events](https://docs.agno.com/teams/running-teams.md)
- [Tasks example and iteration limits](https://docs.agno.com/examples/teams/modes/tasks/basic.md)
- [Official team cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/03_teams)
