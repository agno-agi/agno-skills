# Workflow Reference

Use a workflow when code must control execution order, branching, or approval gates. A [team](teams.md) lets a model choose the coordination instead.

These examples target Agno 3.1.1. Check the installed version before using current imports, CEL expressions, or `HumanReview`; older examples may use different APIs.

## Build a Sequential Pipeline

Standalone script. Requires Agno's OpenAI dependency and `OPENAI_API_KEY`. Keep the project's chosen model provider if it differs.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Step, StepInput, StepOutput, Workflow

writer = Agent(
    model=OpenAIResponses(id="gpt-5.6-luna"),
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
- `step_input.previous_step_content` is the preceding step's content. It is not always a string; structured agent output can be a Pydantic model.
- `step_input.get_step_content("Prepare")` reads a named earlier step. `get_step_output()` returns its `StepOutput`.
- `additional_data` carries per-run application data. Use `(step_input.additional_data or {})` when reading optional values.
- Return `StepOutput(content=..., stop=True)` to stop early. Use `output_schema` on agents when downstream code requires typed output.
- `Step(add_workflow_history=True, num_history_runs=3)` adds **previous workflow runs**, not the preceding step's output. Configure a database for persisted history. `Workflow(add_workflow_history_to_steps=True)` enables it across steps.

A function used as `Step(executor=...)` takes `StepInput`. A function used as the entire `Workflow(steps=...)` instead receives `(workflow: Workflow, execution_input: WorkflowExecutionInput)`. Import `WorkflowExecutionInput` from `agno.workflow`; do not use old `(session_state, topic)` signatures.

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

In Agno 3.1.1, sync and async generator step executors can yield `StepProgress(content="Indexed one page", data={"processed": 1})` before their final `StepOutput`. Import `StepProgress` from `agno.workflow.types`. With `stream=True, stream_events=True`, these updates arrive as `StepProgressEvent` objects from `agno.run.workflow`, with workflow/step identity and a retry-attempt number. They do not create extra executor runs or become the final result. Use them for UI progress; yield the result as the final `StepOutput`.

## Add Branches, Loops, or Parallel Work

All building blocks are exported by `agno.workflow`.

| Building block | Configuration | Important detail |
| --- | --- | --- |
| `Steps` | `Steps(name="Drafting", steps=[prepare_step, draft_step])` | Named sequential group. |
| `Parallel` | `Parallel(step_a, step_b, name="Reviews")` | Independent branches; sync uses threads, async uses concurrent tasks. |
| `Condition` | `Condition(evaluator=check, steps=[yes_step], else_steps=[no_step])` | Callable takes `StepInput` and returns a bool. Branches are **lists**, even for one step. |
| `Loop` | `Loop(steps=[draft_step, review_step], max_iterations=3, end_condition=done)` | `done(outputs)` takes a list of `StepOutput`; `True` stops. |
| `Router` | `Router(selector=select, choices=[quick_step, detailed_step])` | Selector takes `StepInput`; return a choice, choice name, or list of choices. |

The table shows configuration shapes, not a complete script: define the named steps and callbacks first. Use unique step names. Set `forward_iteration_output=True` on a `Loop` when each iteration must receive the previous iteration's final output; the default is `False`. Keep retryable steps idempotent, and do not share mutable agent/tool state between parallel branches.

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

- Condition and Router expose `input`, `previous_step_content`, `previous_step_outputs`, `additional_data`, and `session_state`. Text inputs/outputs are converted to strings for CEL.
- Router also exposes `step_choices`. Its CEL selector must return a name present in `choices`, for example `'input.contains("brief") ? "Quick" : "Detailed"'`.
- Loop exposes `current_iteration` (one-based), `max_iterations`, `all_success`, `last_step_content`, and `step_outputs`. For example, `end_condition="all_success && current_iteration >= 2"` stops after a successful second iteration.

Validate expressions and test both branches. Missing CEL support or evaluation errors can produce fallback control flow instead of raising; do not treat an untested expression as an authorization gate.

## Pause for Human Review

Standalone, model-free local example. Requires the SQLite dependency. Use `HumanReview` rather than legacy flat HITL arguments on `Step`.

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

For async code, use `await workflow.arun(...)` and `await workflow.acontinue_run(result)`. The example handles only step confirmation. User-input, output-review, and nested agent/tool pauses have different requirements; resolve the returned requirements before continuing. Do not auto-approve them in a service.

A database preserves paused runs across requests. Save the run/session IDs and reconstruct the same workflow definition before loading with `get_run_output()` / `aget_run_output()` and continuing. Enforce caller ownership before reading or resuming a run. Persisting a paused run is not the same as automatically recovering a crashed execution.

## Background vs Durable Execution

- `await workflow.arun(..., background=True)` starts work in the current process. Keep its event loop alive. A workflow database lets you inspect persisted status, but does not turn that task into a crash-safe queue.
- For durable service submissions, configure [AgentOS](agentos.md) with `QueueConfig(durable=True)` and a supported queue database; prefer PostgreSQL for both jobs and sessions. Submit with `background=true, stream=false` to receive a persisted acceptance and a run ID.
- The default queue `max_attempts=1` makes a lost worker fail visibly instead of replaying side effects. Larger attempt budgets can repeat the whole run; make tools idempotent. Do not promise exactly-once execution.
- Continue queue-owned paused workflows through the service's continue endpoint with `background=true` and resolved `step_requirements`. An inline SDK continuation is not a replacement for the durable queue flow.

## Current Sources

- [Building workflows](https://docs.agno.com/workflows/building-workflows.md) and [running workflows](https://docs.agno.com/workflows/running-workflows.md)
- [HumanReview](https://docs.agno.com/workflows/hitl/human-review.md) and [pause anatomy](https://docs.agno.com/workflows/hitl/pause-anatomy.md)
- [CEL expressions](https://docs.agno.com/agent-os/studio/cel-expressions.md)
- [Durable queue](https://docs.agno.com/agent-os/background-execution/durable-queue.md) and [durable continuations](https://docs.agno.com/agent-os/background-execution/hitl-continuations.md)
- [Official workflow cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/04_workflows)
