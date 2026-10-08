# When Docs Are Incomplete

Use this reference when the public guide/index does not cover the requested behavior, an example fails against the project pin, or the task extends Agno itself. Do not label a feature unsupported just because its documentation is missing.

## Follow the Implemented Path

1. Read the relevant Markdown guide and matching example. Search the live `llms.txt` for other names before calling the feature undocumented.
2. Locate the project's installed source or a nearby Agno checkout. Check the installed package with `python -c "from importlib.metadata import version; print(version('agno'))"`; inspect checkout revision/status and preserve local changes.
3. Match the installed release. With a checkout, read `git show v<version>:libs/agno/agno/<path>` when local `main` is newer. Separate released code, tracked newer code, and uncommitted additions.
4. Search `libs/agno/agno`, `cookbook`, and `libs/agno/tests` with `rg`. Start at public exports/constructor, then follow initialization, execution, storage, and API routing. Read tests as contract evidence.
5. Confirm imports/signatures, sync/async support, required backends, identity propagation, and failure behavior. Report source evidence and what remains unverified. A cookbook or test name is not proof that the user's runtime works.

If local source is unavailable, inspect the matching [release](https://github.com/agno-agi/agno/releases), [SDK source](https://github.com/agno-agi/agno/tree/main/libs/agno/agno), and [cookbook](https://github.com/agno-agi/agno/tree/main/cookbook). Use private helpers to understand behavior rather than presenting them as stable application APIs.

## Scorers and Rollout Environments

Both packages ship in the SDK but may lack dedicated guides. Search the docs index first; use the source below when it has no matching route.

- [Scorer exports](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/scorer/__init__.py): `Score`, `Scorer`, `CodeScorer`, `JudgeScorer`, and `ToolCallScorer`. Read `base.py`, `code.py`, `judge.py`, and `tools.py` for expected-value handling and scoring contracts. Scores use `[0, 1]`; judge calls add model cost.
- [Environment exports](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/environments/__init__.py): `Environment`, `Task`, `run_rollouts` / `arun_rollouts`, results/diffs, and `to_sft_jsonl` / `ato_sft_jsonl`. Read `environment.py`, `runner.py`, and `exporters/sft.py` for task shape, fingerprints, repeated attempts, and export eligibility.
- Attempts isolate built-in session state and caches, but custom tools/hooks and global tracing can still have effects. Live agents holding MCP connections need per-attempt factories. Use the installed runner's isolation path rather than assuming a rollout is a sandbox.
- SFT export defaults to passing attempts. Inspect its export report and fingerprint compatibility; do not treat a sampled pass as a measured pass rate or an export as completed training.

### Score Repeated Attempts

Save as a Python file so the scorer's source can be fingerprinted. Requires `agno[openai]`. Executing the main block makes model calls and writes an export; keep it separate from serving imports.

```python
from agno.agent import Agent
from agno.environments import Environment, Task, run_rollouts, to_sft_jsonl
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunOutput
from agno.scorer import CodeScorer


def exact_answer(run: RunOutput, expected: str) -> bool:
    return isinstance(run.content, str) and run.content.strip() == expected


environment = Environment(
    name="capital-answers",
    agent=Agent(
        model=OpenAIResponses(id="gpt-6.1-sol"),
        instructions="Return only the capital city's name, with no punctuation.",
    ),
    tasks=(
        Task(id="france", input="What is the capital of France?", expected="Paris"),
        Task(id="japan", input="What is the capital of Japan?", expected="Tokyo"),
    ),
    scorer=CodeScorer(exact_answer),
    timeout_seconds=60,
)

if __name__ == "__main__":
    result = run_rollouts(environment, k=3, concurrency=2)
    result.print_report()
    report = to_sft_jsonl(result, "passing-capital-attempts.jsonl")
    print(report)
```

Use `await arun_rollouts(environment, ...)` and `await ato_sft_jsonl(result, ...)` in an existing event loop. For an async scorer, call `await scorer.ascore(...)` rather than its synchronous bridge.

## Follow-up Configuration Ahead of the Guide

The [published followup guide](https://docs.agno.com/agents/usage/agent-with-followup-suggestions.md) documents boolean configuration and warns about model strings. Newer source exposes [`FollowupConfig`](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/agent/followup.py).

The config supports model/instructions and exact or ranged counts; do not combine it with top-level `num_followups` / `followup_model`. The minimum is requested, the maximum enforced. Main instructions/retrieved context are not copied into the suggestion call. Inspect `_init.py` / `_response.py` for model resolution and events.

## Managed Authorization

For behavior beyond the JWT/scopes guides, inspect the [authz exports](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/os/authz/__init__.py): `Authorization`, policy/provider interfaces, user-directory and audit interfaces, and fine-grained authorization adapters.

Read `authorization.py` and `agno/os/app.py` before using managed roles or a custom policy engine. `engine=` substitutes the managed-role backend; `authorization_provider=` is a full provider override and cannot be combined with it. Verification-only setup does not activate managed roles. Configure user isolation separately and authorize custom resources explicitly.

## Custom External Framework Adapters

Read the [multi-framework guide](https://docs.agno.com/agent-os/multi-framework/overview.md) for shipped adapters. For a new framework, inspect [`BaseExternalAgent`](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/agents/base.py): implement `_arun_adapter` and `_arun_adapter_stream`, and retain lifecycle/session integration. Follow a matching adapter under `agno/agents/` for provider-specific history and continuation IDs.

The wrapper does not imply parity with native Agent tools, learning, media, approvals, or cancellation. Inspect the adapter and router path for each requested capability. Keep framework session IDs distinct from Agno session IDs.

## More Docs

- [Documentation index](https://docs.agno.com/llms.txt)
- [Scorers](https://github.com/agno-agi/agno/tree/main/libs/agno/agno/scorer) and [rollout environments](https://github.com/agno-agi/agno/tree/main/libs/agno/agno/environments)
- [Authorization source](https://github.com/agno-agi/agno/tree/main/libs/agno/agno/os/authz)
