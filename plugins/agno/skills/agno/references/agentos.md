# AgentOS Services and Operations

Use AgentOS when agents, teams, or workflows need an HTTP, MCP, or messaging surface. The runtime runs in your environment; connecting the hosted Control Plane is optional. See [Agents as API](https://docs.agno.com/use-cases/agents-as-api.md) and [Build](build.md).

## Minimal Local Service

Install `agno[os,openai,sqlite]` and set `OPENAI_API_KEY`. Save as `app.py`; this local example is **not authenticated**. Model calls require access to the selected model.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.os import AgentOS

db = SqliteDb(db_file="tmp/agentos.db")
assistant = Agent(
    id="assistant",
    model=OpenAIResponses(id="gpt-5.6-luna"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)
agent_os = AgentOS(id="local-assistant", agents=[assistant], db=db)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="app:app", host="127.0.0.1", port=7777, reload=False)
```

Run `python app.py`, then inspect `/health` and `/docs`. The core run endpoint accepts **form data**, not an assumed JSON chat schema:

```bash
curl http://localhost:7777/agents/assistant/runs \
  -F 'message=Hello' -F 'session_id=local-demo' -F 'stream=false'
```

Keep the returned `session_id` for follow-up messages and `run_id` for lifecycle actions. Use `stream=true` for SSE and parse typed events. Derive the actual URL and port from the project rather than copying this port into a deployment.

## Production Identity and Data Boundaries

Read [Security & Auth](https://docs.agno.com/features/security-and-auth.md) and the [AuthorizationConfig reference](https://docs.agno.com/reference/agent-os/authorization-config.md). Add authentication **before** exposing the service. RS256 verification also needs `PyJWT[crypto]`; install it in the project environment (for example, `uv pip install "PyJWT[crypto]"`). The base AgentOS extra does not guarantee this dependency. This replacement constructor extends the local example above; configure a production database separately:

```python
from os import environ

from agno.os.config import AuthorizationConfig

agent_os = AgentOS(
    id="product-agent-os",
    agents=[assistant],
    db=db,
    authorization=True,
    authorization_config=AuthorizationConfig(
        verification_keys=[environ["JWT_VERIFICATION_KEY"]],
        algorithm="RS256",
        verify_audience=True,
        audience="product-agent-os",
        user_isolation=True,
    ),
    cors_allowed_origins=["https://app.example.com"],
)
app = agent_os.get_app()
```

- The key must match your issuer and algorithm. Use a verified JWT subject for user identity; do not trust a client-supplied `user_id` or treat a session ID as a credential.
- Grant minimal scopes such as `agents:assistant:run`. Do not give end users `agent_os:admin`; admins bypass user isolation.
- Authorization does not turn on persistent user isolation for JWT callers. Explicitly opt in. Review shared/unowned data and tool/backend access separately.
- AgentOS copies registered components for core run routes, but some resources are shared. Custom tool state, MCP credentials, and database connections must be concurrency-safe and user-scoped where needed.
- The 3.1 `agno.os.authz` package adds role stores, policies, audit records, user directories, and native/fine-grained authorization engines. Read the matching release and security guides before enabling these; do not mix legacy config and a new policy setup without checking their interaction.
- Protect custom routes explicitly. Health/discovery routes and MCP server cards can be public. Messaging interfaces have their own request verification; MCP OAuth is a separate surface.
- Use PostgreSQL for shared persistence, HTTPS, restricted CORS, and gateway rate limits. Keep tokens, verification material, and database credentials out of logs and committed files.

Test with two non-admin identities: creation, list/read, continuation, cancellation, and reconnect must enforce ownership. Also test missing/invalid tokens and forbidden scopes. A successful health check proves none of these boundaries.

## Background Work, Reconnect, and Recovery

Read [background execution](https://docs.agno.com/background-execution/overview.md), the [durable queue](https://docs.agno.com/agent-os/background-execution/durable-queue.md), and [multi-replica setup](https://docs.agno.com/agent-os/background-execution/multi-replica.md). Confirm the configured runtime's API schema.

| Need | Configure and verify |
| --- | --- |
| Return before completion | Submit a background run; persist and use its run/session IDs |
| Reconnect after SSE disconnect | Use the documented replay/cursor mechanism; handle duplicate events |
| Resume after worker/process failure | Configure the durable queue/worker and checkpoint strategy; background mode alone is not this guarantee |
| Several replicas | Shared database plus the documented distributed coordination/event-stream backend; in-memory buffers do not span replicas |
| Pause for approval | Persist requirements and continue the same run after authorized approval, rather than starting another run |
| Cancel work | Use the cancellation API and inspect status/`cancellation_stage`; cancellation does not undo external side effects |

`QueueConfig(durable=True)` opts into durable execution; default background work stays in-process. Accepted durable submissions use `background=true, stream=false` and return HTTP 202 with IDs. Keep durable job storage distinct from Redis coordination. The default `max_attempts=1` does not retry a lost worker; a larger budget can repeat side effects. Some payloads are not queue-compatible: verify admission, restart recovery, and idempotency, not just browser reconnect.

SSE `/resume` replays retained events after `last_event_index`; it does not restart work. Database replay requires stored events. [Checkpoints](https://docs.agno.com/examples/agent-os/run-lifecycle/checkpoints.md) and `/continue` with `continue_from` are a different recovery path. Authorize all lifecycle operations with the run and session ownership information required by the installed version.

## Capabilities to Add Only When Needed

| Capability | Guide and decision |
| --- | --- |
| MCP serving and client auth | [MCP](mcp.md); explicitly choose published tools and lifecycle tools |
| Slack, Telegram, WhatsApp, AG-UI, A2A | [Interfaces](https://docs.agno.com/use-cases/product-agents/interfaces.md); use the interface's verification and optional dependencies |
| Existing non-Agno agents | [Multi-framework integrations](https://docs.agno.com/agent-os/multi-framework/overview.md); native Agno features do not automatically apply to wrapped runtimes |
| Remote agents/teams/workflows | [Remote execution](https://docs.agno.com/agent-os/remote-execution/overview.md); distinguish transport/session records from remote execution recovery |
| Bounded public access | [PublicSurface](https://docs.agno.com/agent-os/public-surface.md); explicitly select components, quotas, and tool exposure instead of disabling auth globally |
| Scheduled runs | [Scheduling](https://docs.agno.com/features/scheduling.md); persist schedules, select timezones/retries, and test duplicate-run handling |
| Registry and Studio | [Components](https://docs.agno.com/examples/components/overview.md); preserve stable IDs and register non-serializable tools, schemas, and dependencies |
| Durable files and checkpoints | [FileSystem](https://docs.agno.com/filesystem/overview.md); scope namespaces/users and do not store secrets |
| OpenTelemetry traces | [Tracing](https://docs.agno.com/tracing/overview.md); configure dependencies/storage, then enable `tracing=True` |
| Quality and regression checks | [Evals](https://docs.agno.com/evals/overview.md) and [eval suites](https://docs.agno.com/evals/suite/overview.md) |

**Filesystem upgrade warning:** 3.1 re-keys `DbFileSystem` storage by namespace, user, and path. Older tables require the database-specific filesystem migration with the application stopped. It is separate from `MigrationManager`; read the [3.1.0 release notes](https://github.com/agno-agi/agno/releases/tag/v3.1.0), back up data, and obtain approval before running it.

## Evaluation and Observability

- Use accuracy or model-as-judge evaluations for answer quality, reliability evaluations for tool behavior, and performance evaluations for latency/memory. A syntax check is not an agent evaluation.
- Use `Case`, `cli`, `run_cases`, and `arun_cases` from `agno.eval` for repeatable suites, tag selection, timeouts, JSON reports, and CI exit codes. Cases can combine criteria, expected tool calls, and scorers. Control judge model choice, cost, and variability.
- Trace representative success, tool failure, and cancellation paths. Inspect retrieved sources and approvals, not only the final answer.
- Apply data retention and redaction policies to prompts, tool arguments, traces, and evaluation outputs.
- Connect the actual AgentOS URL to [os.agno.com](https://os.agno.com) only when requested. Confirm visibility there separately from local API success.
