# Agent Reference

## Creating an Agent

```python
from agno.agent import Agent

agent = Agent(
    # --- Identity ---
    name="My Agent",                    # Display name
    id="my-agent",                      # Unique identifier
    model="openai:gpt-4o",             # Model (string shorthand or Model instance)

    # --- Instructions ---
    description="Agent description",    # Added to system message
    instructions=["Rule 1", "Rule 2"], # List of strings or single string
    system_message="Full override",     # Replaces auto-generated system message
    expected_output="Format spec",      # Output format guidance
    additional_context="Extra info",    # Appended to system message

    # --- Tools ---
    tools=[YFinanceTools()],           # List of Toolkit, Callable, or Function
    tool_call_limit=10,                # Max tool calls per run
    tool_choice="auto",                # "auto", "none", "required", or {"type": "function", "function": {"name": "..."}}
    tool_hooks=[my_hook],              # Hooks called on tool execution

    # --- Structured Output ---
    output_schema=MyPydanticModel,     # Pydantic model for typed responses
    structured_outputs=True,           # Use native structured outputs (provider support required)
    use_json_mode=False,               # Force JSON mode

    # --- Session & Storage ---
    db=SqliteDb(db_file="agents.db"),  # Database for session persistence
    session_id="session-123",          # Persistent session identifier
    user_id="user@example.com",        # User identifier for memory/learning
    add_history_to_context=True,       # Include conversation history
    num_history_runs=5,                # Number of past runs to include

    # --- Memory ---
    memory_manager=MemoryManager(...), # User memory manager
    enable_agentic_memory=True,        # Agent decides when to store/recall (efficient)
    update_memory_on_run=False,        # Auto-extract after every run (guaranteed but costly)

    # --- Knowledge (RAG) ---
    knowledge=knowledge_base,          # KnowledgeBase instance
    add_knowledge_to_context=True,     # Add retrieved docs to context

    # --- Learning ---
    learning=LearningMachine(...),     # Or learning=True for defaults

    # --- State ---
    session_state={"key": "value"},    # Shared state dict
    add_session_state_to_context=True, # Include state in context

    # --- Reasoning ---
    reasoning=True,                    # Enable chain-of-thought
    reasoning_model=Model(...),        # Separate model for reasoning
    reasoning_min_steps=1,
    reasoning_max_steps=10,

    # --- Hooks & Guardrails ---
    pre_hooks=[guardrail_fn],          # Run before agent response
    post_hooks=[eval_fn],              # Run after agent response

    # --- Context Enrichment ---
    add_datetime_to_context=True,      # Add current date/time
    add_location_to_context=False,     # Add user location
    add_name_to_context=False,         # Add agent name

    # --- Retry & Reliability ---
    retries=0,                         # Number of retries on failure
    delay_between_retries=1,           # Seconds between retries
    exponential_backoff=False,         # Exponential backoff on retries

    # --- Streaming ---
    stream=True,                       # Enable streaming
    stream_events=False,               # Enable event-based streaming

    # --- Debug ---
    debug_mode=False,                  # Detailed logging
    telemetry=True,                    # Usage telemetry (set False to disable)
    markdown=True,                     # Format output as markdown
)
```

## Key Methods

### run() / arun()

Execute the agent and get a RunOutput.

```python
# Synchronous
response = agent.run("Your message")
print(response.content)  # String or Pydantic model if output_schema set

# Asynchronous
response = await agent.arun("Your message")

# With streaming
for chunk in agent.run("Your message", stream=True):
    print(chunk)

# With multimodal inputs
from agno.media import Image
response = agent.run(
    "Describe this image",
    images=[Image(url="https://example.com/photo.jpg")],
)

# Override parameters per-run
response = agent.run(
    "Your message",
    session_id="custom-session",
    user_id="user@example.com",
    debug_mode=True,
)
```

### print_response() / aprint_response()

Execute and print formatted output to console.

```python
# Basic
agent.print_response("Your message", stream=True)

# Async
await agent.aprint_response("Your message", stream=True)

# With options
agent.print_response(
    "Your message",
    stream=True,
    markdown=True,
    show_reasoning=True,
    session_id="my-session",
    user_id="user@example.com",
)
```

### Memory Methods

```python
# Get user memories
memories = agent.get_user_memories(user_id="user@example.com")
```

## RunOutput

The response object from `agent.run()`:

```python
response = agent.run("message")

response.content          # str or BaseModel (if output_schema)
response.messages         # List of messages exchanged
response.metrics          # Token usage, timing, etc.
response.run_id           # Unique run identifier
response.session_id       # Session identifier
```

## Input Types

Agents accept flexible input:

```python
# String
agent.run("Hello")

# Message object
from agno.models.message import Message
agent.run(Message(role="user", content="Hello"))

# List of messages
agent.run([
    Message(role="user", content="Hello"),
    Message(role="assistant", content="Hi!"),
    Message(role="user", content="Follow up"),
])

# Dict
agent.run({"role": "user", "content": "Hello"})

# Pydantic model (when using input schema)
agent.run(MyInputModel(field="value"))
```

## Multimodal Support

```python
from agno.media import Audio, Image, Video, File

agent.run("Describe this", images=[Image(url="https://...")])
agent.run("Transcribe this", audio=[Audio(filepath="audio.mp3")])
agent.run("Analyze this", videos=[Video(url="https://...")])
agent.run("Read this", files=[File(filepath="doc.pdf")])
```
