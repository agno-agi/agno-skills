# Model Providers Reference

Docs: [Models](https://docs.agno.com/models/overview.md).

Keep the user's provider, endpoint, and model unless a required capability is missing. Compatibility depends on all three: adapter, endpoint, and model ID.

## Configure an Explicit Adapter

Requires Agno and the provider SDK. For a new environment: `uv pip install "agno[openai]"`; otherwise retain pins. Construction needs no network or key:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

model = OpenAIResponses(
    id="gpt-6.1-sol",
    max_output_tokens=1024,
    timeout=30.0,
)
agent = Agent(model=model)
```

Execution needs `OPENAI_API_KEY`, network access, and account access to the model. Store secrets outside source code.

Prefer an explicit adapter when API family/configuration matters; string aliases and defaults can change between releases.

## Find the Right Integration

Selected imports follow. Install the provider SDK, configure authentication, and select an authorized model ID.

| Provider/path | Import | Configuration to verify |
| --- | --- | --- |
| OpenAI Responses API | `from agno.models.openai import OpenAIResponses` | `OPENAI_API_KEY`, model access |
| Anthropic | `from agno.models.anthropic import Claude` | Anthropic SDK, `ANTHROPIC_API_KEY` |
| Google Gemini | `from agno.models.google import Gemini` | `google-genai`, Google API or Vertex configuration |
| AWS Bedrock Converse | `from agno.models.aws import AwsBedrock` | AWS SDKs, region, credentials, model access |
| Azure OpenAI Responses | `from agno.models.azure import AzureOpenAIResponses` | OpenAI SDK, Azure endpoint, `id` = deployment name, supported API version |

## OpenAI-Compatible Endpoints

Use the adapter for the actual protocol:

- Chat Completions-compatible API: `OpenAILike` from `agno.models.openai.like`.
- Open Responses-compatible API: `OpenResponses` from `agno.models.openai`.
- Prefer a dedicated provider adapter when it implements features your application needs.

Set `id`, `base_url`, and `api_key` explicitly to the project's authorized values. API-format compatibility does **not** guarantee tools, structured output, streaming, or media support.

## Parameters Are Not Universal

- `OpenAIResponses` uses `max_output_tokens`, not `max_tokens`. Reasoning, sampling, verbosity, and service-tier values are model-specific.
- Set `output_schema` on the Agent or run; validate [typed results](examples.md).
- Provider request retries and Agent run retries differ. Make side-effecting tools idempotent before retrying.
- Provider storage and Agno `db` persistence are separate privacy settings.
- Use [async Agent APIs](agents.md), not an invented async model class; custom I/O must also be nonblocking.

## More Docs

- [Provider index](https://docs.agno.com/models/providers/model-index.md) and [compatibility](https://docs.agno.com/models/compatibility.md)
- [OpenAI Responses](https://docs.agno.com/models/providers/native/openai/responses/overview.md)
- [OpenAI-compatible APIs](https://docs.agno.com/models/providers/openai-like.md)
- [Caching](https://docs.agno.com/models/cache-response.md) and [fallback models](https://docs.agno.com/models/fallback-models.md)
- [Official model cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/90_models)
