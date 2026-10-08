# Docs Map

Use this map to select a guide, then fetch its Markdown and relevant links. The live [docs index](https://docs.agno.com/llms.txt) is authoritative for individual integrations and new topics.

Source paths below are relative to `libs/agno/` in an Agno checkout. Match the installed release; use [source gaps](source-gaps.md) when the guide omits the needed behavior.

| Feature family | Markdown entry | Source area |
| --- | --- | --- |
| Agents, run APIs, streaming, events | [Agents](https://docs.agno.com/agents/overview.md) | `agno/agent/`, `agno/run/` |
| Team modes, delegation, task planning | [Teams](https://docs.agno.com/teams/overview.md) | `agno/team/` |
| Workflow patterns, nested steps, review gates | [Workflows](https://docs.agno.com/workflows/overview.md) | `agno/workflow/` |
| Structured I/O, parser/output models | [Input & output](https://docs.agno.com/input-output/overview.md) | `agno/agent/_response.py`, `agno/team/_response.py` |
| Model/provider APIs, retries, caching, fallbacks | [Models](https://docs.agno.com/models/overview.md) | `agno/models/` |
| Images, audio, video, files | [Multimodal](https://docs.agno.com/multimodal/overview.md) | `agno/media/`, selected model adapter |
| Session persistence, history, summaries, storage controls | [Sessions](https://docs.agno.com/sessions/overview.md) | `agno/session/`, component `_storage.py` |
| Media offload and object storage | [Media storage](https://docs.agno.com/sessions/persisting-sessions/media-storage/overview.md) | `agno/media/storage/` |
| Instructions and context construction | [Context](https://docs.agno.com/context/overview.md) | component `_messages.py` |
| Tool-result compression | [Compression](https://docs.agno.com/compression/overview.md) | `agno/compression/` |
| Large tool/member result offloading | [Result offloading](https://docs.agno.com/examples/agents/result-offloading/offload-tool-results.md) | `agno/offload/` |
| Session state and injected dependencies | [State](https://docs.agno.com/state/overview.md), [dependencies](https://docs.agno.com/dependencies/overview.md) | component `_session.py`, `_tools.py` |
| Memory and learning stores | [Memory](https://docs.agno.com/memory/overview.md), [learning](https://docs.agno.com/learning/overview.md) | `agno/memory/`, `agno/learn/` |
| Durable notes and filesystem backends | [FileSystem](https://docs.agno.com/filesystem/overview.md) | `agno/fs/` |
| RAG, readers, chunks, filters, rerankers | [Knowledge](https://docs.agno.com/knowledge/overview.md) | `agno/knowledge/`, `agno/vectordb/` |
| Published documentation pages | [Published pages](https://docs.agno.com/knowledge/published-pages.md) | `agno/knowledge/page/` |
| Database, vector-store, embedder integrations | [Database](https://docs.agno.com/database/overview.md), [knowledge](https://docs.agno.com/knowledge/overview.md) | `agno/db/`, `agno/vectordb/`, `agno/knowledge/embedder/` |
| Custom tools and integration catalog | [Tools](https://docs.agno.com/tools/overview.md) | `agno/tools/` |
| Context providers and custom providers | [Context providers](https://docs.agno.com/context-providers/overview.md) | `agno/context/` |
| Load instructions/scripts as skills | [Skills](https://docs.agno.com/skills/overview.md) | `agno/skills/` |
| Native/separate-model reasoning | [Reasoning](https://docs.agno.com/reasoning/overview.md) | `agno/reasoning/`, selected adapter |
| Run hooks and guardrails | [Hooks](https://docs.agno.com/hooks/overview.md), [guardrails](https://docs.agno.com/guardrails/overview.md) | `agno/hooks/`, `agno/guardrails/` |
| Confirmation, input, external execution, approval records | [HITL](https://docs.agno.com/hitl/overview.md), [approval](https://docs.agno.com/hitl/approval.md) | `agno/approval/`, `agno/run/requirement.py`, `agno/run/approval.py` |
| Cancellation and background SDK execution | [Cancellation](https://docs.agno.com/run-cancellation/overview.md), [background](https://docs.agno.com/background-execution/overview.md) | `agno/run/`, component `_run.py` |
| FastAPI serving, custom app/routes/lifespan | [AgentOS](https://docs.agno.com/agent-os/introduction.md), [lifespan](https://docs.agno.com/agent-os/lifespan.md) | `agno/os/app.py`, `agno/os/routers/` |
| Authentication, RBAC, user isolation, machine tokens | [Security](https://docs.agno.com/agent-os/security/overview.md) | `agno/os/authz/`, `agno/os/middleware/`, service-account router |
| Public components and bounded access | [Public surface](https://docs.agno.com/agent-os/public-surface.md) | `agno/os/public/` |
| Per-request agents/teams/workflows | [Factories](https://docs.agno.com/agent-os/factories/overview.md) | `agno/factory/`, component `factory.py` |
| Studio components, registry, builder tools | [Studio](https://docs.agno.com/agent-os/studio/introduction.md) | `agno/registry/`, `agno/tools/studio.py` |
| External framework adapters | [Multi-framework](https://docs.agno.com/agent-os/multi-framework/overview.md) | `agno/agents/` |
| MCP clients, serving, OAuth, lifecycle | [Consume](https://docs.agno.com/tools/mcp/overview.md), [serve](https://docs.agno.com/agent-os/mcp/mcp.md) | `agno/tools/mcp/`, `agno/os/mcp.py` |
| Messaging, A2A, AG-UI interfaces | [Interfaces](https://docs.agno.com/features/interfaces.md) | `agno/os/interfaces/`, `agno/integrations/` |
| Python clients and remote agents/teams/workflows | [Clients](https://docs.agno.com/agent-os/client/overview.md), [remote execution](https://docs.agno.com/agent-os/remote-execution/overview.md) | `agno/client/`, `agno/remote/`, component `remote.py` |
| Durable jobs, replica coordination, replay, recovery | [Background execution](https://docs.agno.com/agent-os/background-execution/overview.md) | `agno/job_queue/`, `agno/os/config.py`, `agno/run/` |
| Schedules and persisted approvals | [Scheduler](https://docs.agno.com/scheduler/overview.md), [approvals](https://docs.agno.com/agent-os/approvals/overview.md) | `agno/scheduler/`, approval router |
| Traces, metrics, performance, quality/reliability evals | [Tracing](https://docs.agno.com/tracing/overview.md), [metrics](https://docs.agno.com/sessions/metrics/overview.md), [evals](https://docs.agno.com/evals/overview.md) | `agno/tracing/`, `agno/metrics.py`, `agno/eval/` |
| Scorers, repeated rollouts, SFT export | [Source gaps](source-gaps.md) | `agno/scorer/`, `agno/environments/` |

For use cases, templates, deployment, CLI, and Control Plane connection, use [Build](build.md). For API field details and migrations, select the current reference/FAQ/release entry from `llms.txt`; do not infer unsupported APIs from a feature heading.

## More Docs

- [SDK introduction](https://docs.agno.com/sdk/introduction.md)
- [SDK source](https://github.com/agno-agi/agno/tree/main/libs/agno/agno)
- [Official cookbook](https://github.com/agno-agi/agno/tree/main/cookbook)
