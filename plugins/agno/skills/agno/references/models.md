# Model Providers Reference

Keep the user's provider, endpoint, and model unless a required capability is missing. An Agno adapter, the provider endpoint, and the selected model ID jointly determine compatibility. Do not infer support from the adapter name alone.

## Configure an Explicit Adapter

Prerequisites: the project's Agno version and provider SDK. For OpenAI, install `uv pip install "agno[openai]"` in a new environment; retain existing pins in an established project. This constructs a model without a network call or API key:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

model = OpenAIResponses(
    id="gpt-5.6-luna",
    max_output_tokens=1024,
    timeout=30.0,
)
agent = Agent(model=model)
```

Execution requires `OPENAI_API_KEY`, network access, and model access. Keep secrets in environment variables or a secret manager, not source code. The example model ID is not a guarantee of account availability.

Use an explicit class when API family or configuration matters. String shorthand is convenient, but provider aliases and defaults can change between releases. Check the installed version before copying one.

## Find the Right Integration

These are selected current imports, not a complete provider catalog. Install each adapter's SDK and follow its authentication guide before execution. Choose model IDs from the provider's current catalog rather than copying an old preview ID.

| Provider/path | Import | Configuration to verify |
| --- | --- | --- |
| OpenAI Responses API | `from agno.models.openai import OpenAIResponses` | `OPENAI_API_KEY`, model access |
| Anthropic | `from agno.models.anthropic import Claude` | Anthropic SDK, `ANTHROPIC_API_KEY` |
| Google Gemini | `from agno.models.google import Gemini` | `google-genai`, Google API or Vertex configuration |
| AWS Bedrock Converse | `from agno.models.aws import AwsBedrock` | AWS SDKs, region, credentials, model access |
| Claude on Bedrock | `from agno.models.aws.claude import Claude` | Anthropic SDK, AWS credentials, Bedrock model ID |
| Azure OpenAI Responses | `from agno.models.azure import AzureOpenAIResponses` | OpenAI SDK, Azure endpoint, deployment, supported API version |
| Mistral | `from agno.models.mistral import MistralChat` | Mistral SDK, `MISTRAL_API_KEY` |
| Local Ollama | `from agno.models.ollama import Ollama` | Ollama client/server and a downloaded model |

For Vertex AI Claude, Azure AI Foundry, gateways, and other local servers, follow the [provider index](https://docs.agno.com/models/providers/model-index.md). Imports and authentication are integration-specific; names such as `Bedrock`, `AWSClaude`, `Mistral`, and `OllamaChat` are not substitutes for the imports above.

## OpenAI-Compatible Endpoints

Use the adapter for the actual protocol:

- Chat Completions-compatible API: `OpenAILike` from `agno.models.openai.like`.
- Open Responses-compatible API: `OpenResponses` from `agno.models.openai`.
- Prefer a dedicated provider adapter when it implements features your application needs.

Both generic adapters accept `id`, `base_url`, and `api_key`. Supply the exact endpoint and model ID authorized for the project. Configure them explicitly instead of accidentally using OpenAI's endpoint or credentials. Compatibility with one API format does **not** imply support for tools, structured output, streaming, or all media types.

See [OpenAI-compatible models](https://docs.agno.com/models/providers/openai-like.md) for complete configuration. `OpenResponses` defaults to `store=False` and does not automatically chain requests via `previous_response_id`; do not assume that this controls a third-party provider's retention policy.

## Parameters Are Not Universal

- For `OpenAIResponses`, the output cap is `max_output_tokens`. Do not copy a generic `max_tokens` constructor into every adapter.
- Reasoning effort, sampling controls, verbosity, service tiers, and token limits depend on the model. Confirm accepted values before setting them.
- `output_schema` belongs on the Agent or run. Native schema support is model-dependent; use [typed extraction](examples.md#2-typed-extraction) and validate the returned content.
- Provider request retries and Agent run retries are different layers. Account for duplicate tool side effects before enabling broad retries.
- Provider response storage is separate from Agno's `db` session persistence. Configure both according to the application's privacy requirements.
- Use the async Agent APIs for async execution; do not invent an async model class name. Check that custom tools and external clients also use nonblocking I/O.

Sources: [model compatibility](https://docs.agno.com/models/compatibility.md), [OpenAI Responses](https://docs.agno.com/models/providers/native/openai/responses/overview.md), and the selected provider's guide. These references use the Agno 3.1.1 API; match source and release notes to older pinned projects.
