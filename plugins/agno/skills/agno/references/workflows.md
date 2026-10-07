# Workflow Reference

Use a workflow when code must control execution order, branching, or approval gates. A [team](teams.md) lets a model choose the coordination instead.

Examples target Agno 3.1.1. Check the installed version, especially for CEL and `HumanReview`.

## Build a Sequential Pipeline

Standalone script. Requires OpenAI and `OPENAI_API_KEY`; keep the project's provider choice.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Step, StepInput, StepOutput, Workflow

writer = Agent(
    model=OpenAIResponses(id="gpt-6.1-sol"),
    instructions="Write concise release notes using only the supplied facts.",
)


def prepare(step_input: StepInput) -> StepOutput:
    facts = str(step_input.input or "").strip()
    if not facts:
        raise ValueError("Release facts are required")
    return StepOutput(content=f"Verified release facts: {facts}")


prepare_step = Step(name="Prepare", executor=prepare)
draft_step = Step(name="Draft", agent=writer)
workflow = Workflow(
    id="release-notes",
    name="Release Notes",
    steps=[prepare_step, draft_step],
)

if __name__ == "__main__":
    result = workflow.run("CSV export is in beta, opt-in, and limited to 10,000 rows.")
    print(result.content)
```

Create agents once and reuse them. A `Step` takes exactly one of `agent=`, `team=`, `executor=`, or `workflow=` (a nested workflow).

### Pass Data Between Steps

- `step_input.input` is the original workflow input.
- `step_input.previous_step_content` is the preceding step's content; structured output can be a Pydantic model.
- `step_input.get_step_content("Prepare")` reads a named earlier step. `get_step_output()` returns its `StepOutput`.
- `additional_data` carries per-run application data. Use `(step_input.additional_data or {})` when reading optional values.
- Return `StepOutput(content=..., stop=True)` to stop early. Use `output_schema` on agents when downstream code requires typed output.
- `Step(add_workflow_history=True, num_history_runs=3)` adds **previous workflow runs**, not preceding-step output. Persist history with a database. `Workflow(add_workflow_history_to_steps=True)` enables this across steps.

A `Step(executor=...)` function takes `StepInput`. An entire `Workflow(steps=...)` function receives `(workflow: Workflow, execution_input: WorkflowExecutionInput)`. Import `WorkflowExecutionInput` from `agno.workflow`; old `(session_state, topic)` signatures do not apply.

## Run and Stream Asynchronously

Fragment using `workflow` above. Choose one run style; each call starts a new run. Use `arun()` for async executors and call downstream agents with `await agent.arun(...)` inside them.

```python
import asyncio


async def main():
    result = await workflow.arun("CSV export is now available to beta users.")
    print(result.content)

    # A separate streaming run returns an async iterator, not an awaitable.
    async for event in workflow.arun(
        "Export size is limited to 10,000 rows.",
        stream=True,
        stream_events=True,
    ):
        print(event.event)


if __name__ == "__main__":
    asyncio.run(main())
```

Inside an existing event loop, call `await main()` instead of `asyncio.run(main())`. Sync streaming uses `for event in workflow.run(..., stream=True)`. For formatted output, use `print_response()` or await `aprint_response()`.

In [Agno 3.1.1](https://github.com/agno-agi/agno/releases/tag/v3.1.1), generator executors can use `from agno.workflow.types import StepProgress` and yield `StepProgress(content=..., data=...)` before their final `StepOutput`.

## Add Branches, Loops, or Parallel Work

All building blocks are exported by `agno.workflow`.

| Building block | Configuration | Important detail |
| --- | --- | --- |
| `Steps` | `Steps(name="Drafting", steps=[prepare_step, draft_step])` | Named sequential group. |
| `Parallel` | `Parallel(step_a, step_b, name="Reviews")` | Independent branches; sync uses threads, async uses concurrent tasks. |
| `Condition` | `Condition(evaluator=check, steps=[yes_step], else_steps=[no_step])` | Callable takes `StepInput` and returns a bool. Branches are **lists**, even for one step. |
| `Loop` | `Loop(steps=[draft_step, review_step], max_iterations=3, end_condition=done)` | `done(outputs)` takes a list of `StepOutput`; `True` stops. |
| `Router` | `Router(selector=select, choices=[quick_step, detailed_step])` | Selector takes `StepInput`; return a choice, choice name, or list of choices. |

Define the table's steps and callbacks before use, with unique step names. `Loop(forward_iteration_output=True)` passes the previous iteration's final output onward; default is `False`. Keep retries idempotent and mutable agent/tool state separate between parallel branches.

### Use CEL Instead of a Python Callback

CEL expressions are serializable. Install the optional `cel-python` dependency (or Agno's `cel` extra) in the project environment.

Standalone, model-free example:

```python
from agno.workflow import Condition, Step, StepInput, StepOutput, Workflow


def urgent(step_input: StepInput) -> StepOutput:
    return StepOutput(content="Send to the on-call review queue.")


def normal(step_input: StepInput) -> StepOutput:
    return StepOutput(content="Send to the regular review queue.")


workflow = Workflow(
    steps=[
        Condition(
            evaluator='additional_data.priority > 5',
            steps=[Step(name="Urgent", executor=urgent)],
            else_steps=[Step(name="Normal", executor=normal)],
        ),
    ],
)
print(workflow.run("Review this report", additional_data={"priority": 8}).content)
```

Condition/Loop expressions return booleans; Router expressions return a name from `choices`. See [CEL variables and examples](https://docs.agno.com/agent-os/studio/cel-expressions.md).

Test both branches. Missing CEL support or evaluation errors can trigger fallback control flow instead of raising. Do not use an untested expression as an authorization gate.

## Pause for Human Review

Standalone, model-free example requiring SQLite. Use `HumanReview`, not legacy flat HITL arguments on `Step`.

```python
from agno.db.sqlite import SqliteDb
from agno.workflow import HumanReview, OnReject, Step, StepInput, StepOutput, Workflow


def prepare_report(step_input: StepInput) -> StepOutput:
    return StepOutput(content=f"Prepared report: {step_input.input}")


workflow = Workflow(
    id="approved-report",
    db=SqliteDb(db_file="tmp/approved-report.db"),
    steps=[
        Step(
            name="Prepare report",
            executor=prepare_report,
            human_review=HumanReview(
                requires_confirmation=True,
                confirmation_message="Prepare this report?",
                on_reject=OnReject.cancel,
            ),
        ),
    ],
)
result = workflow.run("Quarterly summary", user_id="demo-user", session_id="report-1")
while result.is_paused:
    for requirement in result.steps_requiring_confirmation:
        answer = input(f"{requirement.confirmation_message} [y/N] ")
        if answer.strip().lower() == "y":
            requirement.confirm()
        else:
            requirement.reject()
    result = workflow.continue_run(result)
print(result.status)
print(result.content)
```

Async equivalents: `await workflow.arun(...)` and `await workflow.acontinue_run(result)`. This example handles only step confirmation. Resolve [other pause requirements](https://docs.agno.com/workflows/hitl/pause-anatomy.md) before continuing; do not auto-approve them.

A database preserves paused runs across requests. Save run/session IDs and reconstruct the same workflow before loading with `get_run_output()` / `aget_run_output()`. Check caller ownership before reading or resuming. Persistence does not automatically recover crashed execution.

## Background vs Durable Execution

- `await workflow.arun(..., background=True)` runs in the current process. Keep its event loop alive; persisted status does not make execution crash-safe.
- For durable submissions and retry policy, follow the [AgentOS queue guide](https://docs.agno.com/agent-os/background-execution/durable-queue.md). Retries can repeat side effects; make tools idempotent.
- Resume queue-owned pauses through the [service continuation flow](https://docs.agno.com/agent-os/background-execution/hitl-continuations.md), not an inline SDK continuation.

## Current Sources

- [Building workflows](https://docs.agno.com/workflows/building-workflows.md) and [running workflows](https://docs.agno.com/workflows/running-workflows.md)
- [HumanReview](https://docs.agno.com/workflows/hitl/human-review.md) and [pause anatomy](https://docs.agno.com/workflows/hitl/pause-anatomy.md)
- [CEL expressions](https://docs.agno.com/agent-os/studio/cel-expressions.md)
- [Durable queue](https://docs.agno.com/agent-os/background-execution/durable-queue.md) and [durable continuations](https://docs.agno.com/agent-os/background-execution/hitl-continuations.md)
- [Official workflow cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/04_workflows)
