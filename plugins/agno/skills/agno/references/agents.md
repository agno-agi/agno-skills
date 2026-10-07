# Agent Reference

Start with the [SDK examples](examples.md). Keep the project's model/database choices and reuse agents.

## Choose the Run API

Foreground execution:

| Need | Call | Result |
| --- | --- | --- |
| Sync response | `agent.run(message, stream=False)` | `RunOutput` |
| Async response | `await agent.arun(message, stream=False)` | `RunOutput` |
| Sync stream | `agent.run(message, stream=True)` | Iterator of events |
| Async stream | `agent.arun(message, stream=True)` | Async iterator of events; do **not** await it |
| Console output | `agent.print_response(message, stream=True)` | Prints the response |
| Async console output | `await agent.aprint_response(message, stream=True)` | Prints the response |

Put async calls inside `async def`. Use `asyncio.run(main())` at script entry, not inside an existing event loop. Async tools and MCP need the [async tool path](tools.md#sync-and-async-toolkits).

Check `status` and pending requirements before treating a `RunOutput` as complete. `messages` contains retained run messages, not necessarily full conversation history. Check structured `content` types before accessing fields. See [Running Agents](https://docs.agno.com/agents/running-agents.md) and [RunOutput](https://docs.agno.com/reference/agents/run-response.md) for fields.

## Stream Text and Observe Events

Requires `agno` and `openai`; function calls need `OPENAI_API_KEY` and model access. Construction is offline.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunEvent

agent = Agent(model=OpenAIResponses(id="gpt-6.1-sol"))


def stream_answer(message: str) -> None:
    for event in agent.run(message, stream=True, stream_events=True):
        if event.event == RunEvent.run_content and isinstance(event.content, str):
            print(event.content, end="", flush=True)
        elif event.event in (
            RunEvent.run_paused,
            RunEvent.run_cancelled,
            RunEvent.run_error,
        ):
            print(event.event)


async def astream_answer(message: str) -> None:
    async for event in agent.arun(message, stream=True, stream_events=True):
        if event.event == RunEvent.run_content and isinstance(event.content, str):
            print(event.content, end="", flush=True)
        elif event.event in (
            RunEvent.run_paused,
            RunEvent.run_cancelled,
            RunEvent.run_error,
        ):
            print(event.event)
```

`stream_events=True` adds lifecycle/tool events. Pause, cancellation, and error events can appear without it. This example only renders output; services must handle those outcomes. A terminal event after cancellation is not success. Text deltas are not completed structured output.

## Configure Only What the Task Needs

| Task | Agent settings |
| --- | --- |
| Identity | Stable `id`; caller-scoped `user_id` and `session_id` per run |
| Behavior | `description`, `instructions`, `markdown` |
| Typed input/output | `input_schema`, `output_schema`; [typed extraction](examples.md#2-typed-extraction) |
| Tools | `tools`, `tool_call_limit`, provider-supported `tool_choice`; [Tools](tools.md) |
| Validation | `pre_hooks`, `post_hooks`; [guardrails](https://docs.agno.com/guardrails/overview.md) |

An explicit `system_message` replaces the generated message; prefer `instructions` to retain assembled context. Configure native reasoning on the model adapter; `reasoning_model` selects a separate model. Debug logs can expose prompts and tool data.

## History, Memory, State, and Knowledge Are Different

| Need | Configuration and constraints |
| --- | --- |
| Continue one conversation | `db`, `add_history_to_context=True`, bounded `num_history_runs` or `num_history_messages`; keep the session ID stable |
| Recall facts across sessions | Configure [LearningMachine](learning.md) or legacy memory; extraction can miss facts and add model calls |
| Track application state | `session_state`; tools use injected `RunContext`. `add_session_state_to_context=True` exposes state to the model |
| Supply runtime services/data | `dependencies`; tools read `run_context.dependencies`. Expose only safe data via `add_dependencies_to_context` |
| Search documents on demand | Configured `Knowledge` with `search_knowledge=True` exposes retrieval; see [Knowledge](knowledge.md) |
| Retrieve documents each run | `add_knowledge_to_context=True` with configured knowledge/retrieval |

`max_tool_calls_from_history` trims prompt history, not stored history. Summaries and `compress_tool_results=True` can reduce context but add model calls and lose detail. Do not combine compression with `offload_tool_results`. See [context engineering](https://docs.agno.com/context/agent/overview.md).

Legacy agentic memory and LearningMachine `user_memory` both register `update_user_memory`; choose one. Isolate shared tools, credentials, and databases by caller. IDs alone do not authorize access.

## Add Context without a Large Tool List

- **[Context Providers](https://docs.agno.com/context-providers/using-providers.md):** pass `tools=provider.get_tools()` and `instructions=provider.instructions()`. Scope source credentials; follow resource-owning providers' async setup/close lifecycle.
- **[Skills](https://docs.agno.com/skills/loading-skills.md):** load trusted instructions/references/scripts with `Skills` and `LocalSkills` from `agno.skills`, then pass `skills=...`. Verify loading; scripts can execute code.
- **[FileSystem](https://docs.agno.com/filesystem/overview.md):** durable agent text on database or local-disk backends, not unrestricted host access. Check installed-version scoping and migration requirements.

## Media Inputs

For `run()` / `arun()`, pass `images`, `audio`, `videos`, or `files` with `Image`, `Audio`, `Video`, or `File` from `agno.media`. Use accessible URLs, paths, or supported content. Verify the [adapter and model support the modality](https://docs.agno.com/models/compatibility.md).

## Pause, Resume, or Serve

- Resolve paused `active_requirements`, then use `continue_run()` / `acontinue_run()`; see [approval](tools.md#approve-before-a-tool-runs).
- `cancel_run(run_id)` / `acancel_run(run_id)` do not reverse external side effects.
- See [AgentOS](agentos.md) for HTTP, authentication, and durable work. Async runs are not automatically durable.

Check uncommon settings in the version-matched [Agent reference](https://docs.agno.com/reference/agents/agent.md).
