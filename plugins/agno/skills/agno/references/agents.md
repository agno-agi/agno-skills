# Agent Reference

Start with the runnable [SDK examples](examples.md). Keep the project's model and database choices. Construct an agent once and reuse it.

## Choose the Run API

These forms assume the normal foreground execution path:

| Need | Call | Result |
| --- | --- | --- |
| Sync response | `agent.run(message, stream=False)` | `RunOutput` |
| Async response | `await agent.arun(message, stream=False)` | `RunOutput` |
| Sync stream | `agent.run(message, stream=True)` | Iterator of events |
| Async stream | `agent.arun(message, stream=True)` | Async iterator of events; do **not** await it |
| Console output | `agent.print_response(message, stream=True)` | Prints the response |
| Async console output | `await agent.aprint_response(message, stream=True)` | Prints the response |

Put async calls inside an `async def`. Use `asyncio.run(main())` at a script entry point, but not inside an already running event loop. Async tools and MCP connections belong on the async path; an `arun()` call alone does not make blocking custom I/O nonblocking.

A non-streaming result exposes `content`, `run_id`, `session_id`, `status`, `is_paused`, `messages`, and `metrics`. Check status or pending requirements before treating a run as complete. `messages` contains the messages retained for that run, not necessarily the full stored conversation. With a Pydantic `output_schema`, check the type of `content` before accessing fields.

See [Running Agents](https://docs.agno.com/agents/running-agents.md) and the [RunOutput reference](https://docs.agno.com/reference/agents/run-response.md).

## Stream Text and Observe Events

Prerequisites: `agno` and `openai`. Construction is offline; calling either function needs `OPENAI_API_KEY` and model access. Both functions reuse one agent.

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

`stream_events=True` adds lifecycle and tool events. Even without it, a stream can contain pause, cancellation, or error events; not every item has text. This example only renders output. A service must handle those outcomes, resume approved runs, and avoid declaring success after cancellation. Do not parse individual text deltas as completed structured output.

## Configure Only What the Task Needs

| Task | Agent settings |
| --- | --- |
| Identity | `name`, stable `id`; pass `user_id` and `session_id` per run in multi-user code |
| Behavior | `description`, `instructions`, `expected_output`, `markdown` |
| Typed input/output | `input_schema`, `output_schema`; see [typed extraction](examples.md#2-typed-extraction) |
| Tools | `tools`, `tool_call_limit`, provider-supported `tool_choice`; see [Tools](tools.md) |
| Pre/post processing | `pre_hooks`, `post_hooks`; validate inputs and outputs with [guardrails](https://docs.agno.com/guardrails/overview.md) |
| Recovery | `retries`, `delay_between_retries`, `exponential_backoff`; make side-effecting tools idempotent before retrying |
| Diagnosis | `debug_mode=True` while debugging; logs can contain prompts and tool data |

An explicit `system_message` replaces the normal generated system message. Prefer `instructions` when you want Agno to assemble context from the other settings. Configure native reasoning on the selected model adapter; use `reasoning_model` only when a separate reasoning model is needed. Do not copy obsolete reasoning flags from an older Agno release.

## History, Memory, State, and Knowledge Are Different

| Need | Configuration and constraints |
| --- | --- |
| Continue one conversation | `db`, `add_history_to_context=True`, bounded `num_history_runs` or `num_history_messages`; keep the session ID stable |
| Recall facts across a user's sessions | Legacy `MemoryManager` with `enable_agentic_memory=True` or `update_memory_on_run=True`, or a configured [LearningMachine](learning.md). Model-driven extraction is not guaranteed and can add model calls. |
| Track application state | `session_state`; opt into prompt exposure with `add_session_state_to_context=True`. Tools can read/update the current run's injected `RunContext`. |
| Supply runtime services or data | `dependencies`; access current values through `run_context.dependencies`. Only enable `add_dependencies_to_context` for data safe to send to the model. |
| Search documents on demand | Attach a configured `Knowledge` and enable `search_knowledge=True` to expose a retrieval tool. See [Knowledge](knowledge.md). |
| Inject retrieved documents each run | `add_knowledge_to_context=True` with configured knowledge/retrieval; this differs from model-selected search. |

Persisted sessions require a database. Bound history before adding more context. `max_tool_calls_from_history` can reduce historical tool exchanges without deleting stored history. Session summaries and `compress_tool_results=True` can reduce prompt size but may add model calls and lose detail. Do not combine tool-result compression with `offload_tool_results`; choose one strategy. See [context engineering](https://docs.agno.com/context/agent/overview.md).

Do not enable legacy agentic memory together with a LearningMachine `user_memory` store: both register an `update_user_memory` tool. Pick one owner for user memory. Shared mutable tools, credentials, and databases also need caller isolation; a `user_id` string alone is not an authorization boundary.

## Add Context without a Large Tool List

- **Context Providers** expose a focused interface over an external source. After configuration, pass `tools=provider.get_tools()` and `instructions=provider.instructions()`. Provision source credentials and scope access in the application. For resource-owning providers, follow their async setup/close lifecycle. See [using providers](https://docs.agno.com/context-providers/using-providers.md).
- **Skills** package reusable instructions, references, and scripts. Load trusted local skills with `Skills` and `LocalSkills` from `agno.skills`, then pass `skills=...`. Verify that the intended skills loaded; scripts can execute code. See [loading skills](https://docs.agno.com/skills/loading-skills.md).
- **Durable FileSystem** stores agent files in a database; it is not unrestricted access to host files. See [FileSystem](https://docs.agno.com/filesystem/overview.md) for user scoping, read-only tools, and migration requirements.

## Media Inputs

`run()` and `arun()` accept `images`, `audio`, `videos`, and `files` using `Image`, `Audio`, `Video`, and `File` from `agno.media`. Supply a real accessible URL, local path, or supported content value. The model adapter and selected model must both support that modality; not every model accepts every input type. See [model compatibility](https://docs.agno.com/models/compatibility.md).

## Pause, Resume, or Serve

- For human approval, inspect `active_requirements` on a paused result and call `continue_run()` or `acontinue_run()` with the decisions. See the [approval example](tools.md#approve-before-a-tool-runs).
- Use `cancel_run(run_id)` / `acancel_run(run_id)` for cancellation; do not assume this reverses external side effects.
- For HTTP serving, background work, durable execution, and authentication, use [AgentOS](agentos.md). An async SDK run is not automatically a durable job.

Check uncommon parameters in the version-matched [Agent reference](https://docs.agno.com/reference/agents/agent.md), not an old constructor copied wholesale.
