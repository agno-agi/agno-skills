# Workflow Reference

## Imports

```python
from agno.workflow import Workflow, Step, Steps, Parallel, Condition, Loop, Router
```

## Creating a Workflow

```python
workflow = Workflow(
    name="My Workflow",
    description="What this workflow does",
    steps=[step1, step2, step3],       # Sequential steps
    db=SqliteDb(db_file="agents.db"),  # Session persistence
    session_id="workflow-session",
    debug_mode=False,
)
```

## Step Types

### Step - Single Unit of Work

```python
step = Step(
    name="Data Gathering",
    agent=my_agent,                    # Agent to execute
    description="Fetch market data",
    max_retries=3,                     # Retry on failure
    skip_on_failure=False,             # Skip instead of failing workflow
    add_workflow_history=True,         # Include prior step outputs
    num_history_runs=3,                # How many prior runs to include
)
```

A Step can use an agent, team, or custom executor:

```python
# With agent
Step(agent=my_agent)

# With team
Step(team=my_team)

# With custom executor function
def my_executor(input: StepInput) -> StepOutput:
    # Custom logic
    return StepOutput(content="result")

Step(executor=my_executor)
```

### Steps - Sequential Pipeline

```python
pipeline = Steps(
    name="Processing Pipeline",
    steps=[step1, step2, step3],  # Execute in order
)
```

### Parallel - Concurrent Execution

```python
parallel = Parallel(
    step_a,
    step_b,
    step_c,
    name="Parallel Analysis",
)

# Or with list syntax
parallel = Parallel(
    "Parallel Analysis",   # Name as first string arg
    step_a, step_b, step_c,
)
```

### Condition - Conditional Execution

```python
# With callable
condition = Condition(
    evaluator=lambda input: "urgent" in input.input.lower(),
    steps=urgent_step,
    else_steps=normal_step,
    name="Priority Check",
)

# With CEL expression
condition = Condition(
    evaluator='input.contains("urgent")',
    steps=urgent_step,
    else_steps=normal_step,
)
```

CEL variables available: `input`, `previous_step_content`, `previous_step_outputs`, `additional_data`, `session_state`

### Loop - Iterative Execution

```python
loop = Loop(
    steps=[review_step, refine_step],
    max_iterations=3,
    end_condition=lambda outputs: "APPROVED" in outputs[-1].content,
    name="Refinement Loop",
)

# With CEL expression
loop = Loop(
    steps=[review_step],
    max_iterations=5,
    end_condition='last_step_content.contains("DONE")',
)
```

CEL variables: `current_iteration`, `max_iterations`, `all_success`, `last_step_content`, `step_outputs`

### Router - Dynamic Step Selection

```python
router = Router(
    selector=lambda input: simple_step if len(input.input) < 100 else complex_step,
    choices=[simple_step, complex_step],
    name="Complexity Router",
)

# With CEL expression
router = Router(
    selector='input.contains("simple") ? "simple_step" : "complex_step"',
    choices=[simple_step, complex_step],
)
```

## Running Workflows

```python
# Synchronous
response = workflow.run("Input message")
workflow.print_response("Input message", stream=True)

# Asynchronous
response = await workflow.arun("Input message")
await workflow.aprint_response("Input message", stream=True)
```

## Example: Research Pipeline

```python
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools
from agno.workflow import Step, Workflow

data_agent = Agent(
    name="Data Gatherer",
    model=Gemini(id="gemini-3-flash-preview"),
    tools=[YFinanceTools()],
    instructions=["Gather raw market data. Don't analyze, just organize."],
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-3-flash-preview"),
    instructions=["Analyze the data. Identify strengths, weaknesses, red flags."],
)

writer = Agent(
    name="Report Writer",
    model=Gemini(id="gemini-3-flash-preview"),
    instructions=["Write a concise investment brief. Lead with the bottom line."],
    markdown=True,
)

workflow = Workflow(
    name="Research Pipeline",
    steps=[
        Step(name="Gather", agent=data_agent),
        Step(name="Analyze", agent=analyst),
        Step(name="Report", agent=writer),
    ],
)

workflow.print_response("Analyze NVIDIA for investment", stream=True)
```

## Example: Conditional Workflow

```python
from agno.workflow import Workflow, Step, Condition

workflow = Workflow(
    steps=[
        Step(name="Classify", agent=classifier_agent),
        Condition(
            evaluator=lambda input: "technical" in input.previous_step_content.lower(),
            steps=Step(name="Technical", agent=tech_agent),
            else_steps=Step(name="General", agent=general_agent),
        ),
        Step(name="Finalize", agent=writer_agent),
    ],
)
```
