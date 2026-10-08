# AgentOS Services and Operations

Docs: [AgentOS](https://docs.agno.com/agent-os/introduction.md).

Use AgentOS for HTTP, MCP, or messaging access. It runs in your environment; the hosted Control Plane is optional. See [Build](build.md) for deployment.

## Minimal Local Service

Install `agno[os,openai,sqlite]`, set `OPENAI_API_KEY`, and confirm model access. Save as `app.py`. This local starter configures no authentication.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.os import AgentOS

db = SqliteDb(db_file="tmp/agentos.db")
assistant = Agent(
    id="assistant",
    model=OpenAIResponses(id="gpt-6.1-sol"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)
agent_os = AgentOS(id="local-assistant", agents=[assistant], db=db)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="app:app", host="127.0.0.1", port=7777, reload=False)
```

Run `python app.py`; inspect `/health` and `/docs`. Run endpoints accept **form data**:

```bash
curl http://localhost:7777/agents/assistant/runs \
  -F 'message=Hello' -F 'session_id=local-demo' -F 'stream=false'
```

Keep `session_id` for follow-ups and `run_id` for lifecycle actions. Use `stream=true` for typed SSE events. Use the project’s deployment URL, not this example port.

## Production Identity and Data Boundaries

Follow [Security & Auth](https://docs.agno.com/features/security-and-auth.md) and [managed authorization](source-gaps.md). RS256 requires `uv pip install "PyJWT[crypto]"`. Replace the constructor above; configure PostgreSQL separately:

```python
from os import environ

from agno.os.authz import Authorization

agent_os = AgentOS(
    id="product-agent-os",
    agents=[assistant],
    db=db,
    authorization=Authorization(
        verification_keys=[environ["JWT_VERIFICATION_KEY"]],
        algorithm="RS256",
        verify_audience=True,
        audience="product-agent-os",
    ),
    user_isolation=True,
    cors_allowed_origins=["https://app.example.com"],
)
app = agent_os.get_app()
```

- Match keys to the issuer and algorithm. Use a verified JWT subject for identity; never trust client-supplied identity or treat session IDs as credentials.
- Grant minimal scopes such as `agents:assistant:run`. `agent_os:admin` bypasses user isolation.
- JWT scope enforcement defaults off; configured JWT environment keys or `OS_SECURITY_KEY` can still enable authentication. Audience checks and JWT user isolation need explicit opt-in, as above.
- Review shared/unowned data and backend permissions separately. Models, databases, MCP handles, and some tools remain shared across copied runs; keep mutable state concurrency-safe and credentials user-scoped.
- Protect custom routes explicitly with scope mappings; registering a route does not define its permissions. Discovery routes/server cards can remain public; messaging verification and MCP OAuth have separate policies.
- Use HTTPS, restricted CORS, and gateway rate limits. Keep credentials out of logs and committed files.

Test two non-admin identities across create/list/read, continue/cancel, and reconnect. Test missing/invalid tokens, missing subjects, and forbidden scopes. With user isolation, run lifecycle requests need `session_id`; workflow reconnect also needs `workflow_id`. Health checks do not prove isolation.

## Background Work, Reconnect, and Recovery

Read [background execution](https://docs.agno.com/background-execution/overview.md), the [durable queue](https://docs.agno.com/agent-os/background-execution/durable-queue.md), and [multi-replica setup](https://docs.agno.com/agent-os/background-execution/multi-replica.md). Check the installed runtime’s API schema. Background execution requires a database on the agent, team, or workflow; an OS-level queue store is a separate concern.

| Need | Configure and verify |
| --- | --- |
| Return before completion | Background mode, database persistence, and saved run/session IDs |
| Reconnect SSE | `/resume` replays retained events after `last_event_index`; handle duplicates |
| Survive worker loss | Durable queue and supported queue store, not background mode alone |
| Several replicas | Shared database and distributed cancellation/event streaming; buffers default to in-process |
| Approval or cancellation | Authorize lifecycle actions against run/session ownership; cancellation cannot undo side effects |

Default background work stays in-process. `QueueConfig(durable=True)` opts into durable execution with a supported queue store (PostgreSQL recommended). Accepted queueable submissions use `background=true, stream=false` and return HTTP 202. Job storage is separate from Redis coordination. Default `max_attempts=1` does not re-execute lost workers; larger budgets can repeat side effects. Not every payload is queue-compatible. Test admission, restart recovery, and idempotency, not only browser reconnect.

`/resume` does not restart work. Database replay requires `store_events=True`. [Checkpoints](https://docs.agno.com/examples/agent-os/run-lifecycle/checkpoints.md) and `/continue` with `continue_from` provide a separate recovery path. Continue approval-paused runs rather than starting replacements.

## Studio and Custom Agent Platforms

[Studio](https://docs.agno.com/agent-os/studio/introduction.md) is the visual builder for agents, teams, and workflows in the hosted Control Plane, connected to your AgentOS. You can also build **your own agent platform** with the reusable SDK tools, without the hosted UI.

- Define an `agno.registry.Registry` of approved models, tools, and resources. Share it and a component-capable synchronous database with `AgentOS(registry=registry, db=db)`; use PostgreSQL in production. Keep credentials server-side.
- Attach `agno.tools.studio.StudioTools(registry=registry, db=db)` to a builder `Agent` for creation, editing, validation, previews, versioning, and publishing. Serve the builder through AgentOS or run it standalone. Changes start as drafts; publishing activates stored configuration, not infrastructure deployment.
- Connect your UI to `GET /registry`, `/components`, and AgentOS run/continuation APIs. For dispatch without builder mutations, use `agno.tools.studio_runner.StudioRunnerTools` instead of `StudioTools`.
- For MCP, expose the builder through `AgentOS(..., mcp=True)` and `run_agent`/`continue_run`. Directly registering default `StudioTools` as MCP tools rejects approval-gated methods; do not remove approval gates just to register them.
- Treat builder access as privileged. Enforce caller identity, scopes, user isolation, and approval pauses. Review cross-user sharing before publishing; tool selection is not a sandbox.

See [StudioTools](https://docs.agno.com/tools/toolkits/agent-os/studio.md), [Registry](https://docs.agno.com/agent-os/studio/registry.md), and the [Studio cookbooks](https://github.com/agno-agi/agno/tree/main/cookbook/05_agent_os/22_studio).

## Capabilities to Add Only When Needed

Start with [MCP](mcp.md) or [interfaces](https://docs.agno.com/use-cases/product-agents/interfaces.md) when needed; install interface dependencies and configure their request verification. Use [PublicSurface](https://docs.agno.com/agent-os/public-surface.md) for selected public components and quotas, not globally disabled auth. See [scheduling](https://docs.agno.com/features/scheduling.md) and [tracing](https://docs.agno.com/tracing/overview.md) for optional setup.

## Evaluation and Observability

- Use [evals](https://docs.agno.com/evals/overview.md) and [repeatable suites](https://docs.agno.com/evals/suite/overview.md) for answer quality, tool reliability, and performance. Syntax checks are not agent evaluations; budget judge calls separately.
- Trace success, tool failure, and cancellation. Inspect sources and approvals; apply retention and redaction to prompts, tool arguments, traces, and results.
- Connect to [os.agno.com](https://os.agno.com) only when requested. Verify Control Plane visibility separately from local API success.

## More Docs

- [API serving](https://docs.agno.com/use-cases/agents-as-api.md)
- [Official AgentOS cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/05_agent_os)
