# Model Providers Reference

## Usage

Models can be specified as a class instance or string shorthand:

```python
from agno.agent import Agent

# Class instance (full control)
from agno.models.openai import OpenAIChat
agent = Agent(model=OpenAIChat(id="gpt-4o"))

# String shorthand
agent = Agent(model="openai:gpt-4o")
```

## Supported Providers

### Tier 1 - Major Cloud Providers

| Provider | Class | Import | Example |
|----------|-------|--------|---------|
| OpenAI | `OpenAIChat` | `agno.models.openai` | `OpenAIChat(id="gpt-4o")` |
| OpenAI | `OpenAIResponses` | `agno.models.openai` | `OpenAIResponses(id="gpt-5.2")` |
| Anthropic | `Claude` | `agno.models.anthropic` | `Claude(id="claude-sonnet-4-5-20250929")` |
| Google | `Gemini` | `agno.models.google` | `Gemini(id="gemini-3-flash-preview")` |
| AWS Bedrock | `Bedrock` | `agno.models.aws` | `Bedrock(id="anthropic.claude-v2")` |
| AWS Claude | `AWSClaude` | `agno.models.aws` | `AWSClaude(id="claude-sonnet-4-5-20250929")` |
| Azure | `AzureOpenAI` | `agno.models.azure` | `AzureOpenAI(id="gpt-4o", azure_endpoint="...")` |
| Azure | `AzureAIFoundry` | `agno.models.azure` | `AzureAIFoundry(id="...", azure_endpoint="...")` |
| Vertex AI | `VertexAIClaude` | `agno.models.vertexai` | `VertexAIClaude(id="claude-sonnet-4-5-20250929")` |

### Tier 2 - Inference Providers

| Provider | Class | Import | Example |
|----------|-------|--------|---------|
| Groq | `Groq` | `agno.models.groq` | `Groq(id="llama-3.3-70b-versatile")` |
| Mistral | `Mistral` | `agno.models.mistral` | `Mistral(id="mistral-large-latest")` |
| Cohere | `Cohere` | `agno.models.cohere` | `Cohere(id="command-r-plus")` |
| Fireworks | `Fireworks` | `agno.models.fireworks` | `Fireworks(id="...")` |
| Together | `Together` | `agno.models.together` | `Together(id="...")` |
| DeepInfra | `DeepInfra` | `agno.models.deepinfra` | `DeepInfra(id="...")` |
| DeepSeek | `DeepSeek` | `agno.models.deepseek` | `DeepSeek(id="deepseek-chat")` |
| Perplexity | `Perplexity` | `agno.models.perplexity` | `Perplexity(id="...")` |
| OpenRouter | `OpenRouter` | `agno.models.openrouter` | `OpenRouter(id="...")` |
| Cerebras | `Cerebras` | `agno.models.cerebras` | `Cerebras(id="...")` |
| Sambanova | `Sambanova` | `agno.models.sambanova` | `Sambanova(id="...")` |
| Nebius | `Nebius` | `agno.models.nebius` | `Nebius(id="...")` |
| Nvidia | `Nvidia` | `agno.models.nvidia` | `Nvidia(id="...")` |

### Tier 3 - Local & Self-hosted

| Provider | Class | Import | Example |
|----------|-------|--------|---------|
| Ollama | `OllamaChat` | `agno.models.ollama` | `OllamaChat(id="llama3")` |
| LM Studio | `LMStudio` | `agno.models.lmstudio` | `LMStudio(id="...")` |
| Llama.cpp | `LlamaCpp` | `agno.models.llama_cpp` | `LlamaCpp(id="...")` |
| VLLM | `VLLM` | `agno.models.vllm` | `VLLM(id="...")` |
| HuggingFace | `HuggingFace` | `agno.models.huggingface` | `HuggingFace(id="...")` |

### Tier 4 - Routing & Proxy

| Provider | Class | Import | Example |
|----------|-------|--------|---------|
| LiteLLM | `LiteLLMOpenAI` | `agno.models.litellm` | `LiteLLMOpenAI(id="...")` |
| OpenAILike | `OpenAILike` | `agno.models.openai` | `OpenAILike(id="...", api_key="...", base_url="...")` |
| Portkey | `Portkey` | `agno.models.portkey` | `Portkey(id="...")` |
| LangDB | `LangDB` | `agno.models.langdb` | `LangDB(id="...")` |
| Requesty | `Requesty` | `agno.models.requesty` | `Requesty(id="...")` |

## Common Model Parameters

```python
from agno.models.openai import OpenAIChat

model = OpenAIChat(
    id="gpt-4o",                       # Model identifier
    api_key="sk-...",                   # API key (or set env var)
    temperature=0.7,                   # Sampling temperature
    max_tokens=4096,                   # Max output tokens
    top_p=1.0,                         # Nucleus sampling
    frequency_penalty=0.0,             # Frequency penalty
    presence_penalty=0.0,              # Presence penalty
    stop=["END"],                      # Stop sequences
)
```

## OpenAI-Compatible Providers

Use `OpenAILike` for any OpenAI-compatible API:

```python
from agno.models.openai import OpenAILike

model = OpenAILike(
    id="my-model",
    api_key="my-api-key",
    base_url="https://my-provider.com/v1",
)
```
