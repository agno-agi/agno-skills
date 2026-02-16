# Team Reference

## Creating a Team

```python
from agno.agent import Agent
from agno.team.team import Team

team = Team(
    # --- Required ---
    members=[agent1, agent2],          # List of Agent or Team instances

    # --- Identity ---
    name="My Team",
    model=Gemini(id="gemini-3-flash-preview"),  # Leader model
    role="Team leader role description",

    # --- Execution Mode ---
    mode="coordinate",                 # coordinate, route, broadcast, tasks
    respond_directly=False,            # Members respond directly to user
    max_iterations=10,                 # Max coordination loops

    # --- Instructions ---
    instructions=["Instruction 1"],
    description="Team description",

    # --- Member Coordination ---
    show_members_responses=True,       # Show individual member responses
    add_team_history_to_members=False, # Share team history with members
    share_member_interactions=False,   # Members see each other's responses

    # --- Session & Storage ---
    db=SqliteDb(db_file="agents.db"),
    session_id="team-session",
    user_id="user@example.com",
    add_history_to_context=True,
    num_history_runs=5,

    # --- Output ---
    output_schema=MyModel,             # Structured output
    markdown=True,
)
```

## Team Modes

### coordinate (default)
Supervisor pattern. Leader picks members, crafts tasks, synthesizes responses.
```python
team = Team(members=[agent1, agent2], mode="coordinate")
```

### route
Router pattern. Leader routes to a single specialist and returns their response directly.
```python
team = Team(
    members=[finance_agent, legal_agent, tech_agent],
    mode="route",
)
# Leader picks the best-fit agent for each query
```

### broadcast
Fan-out pattern. Leader sends the same task to all members simultaneously.
```python
team = Team(
    members=[bull_agent, bear_agent],
    mode="broadcast",
)
# All members process the task, leader synthesizes
```

### tasks
Autonomous task decomposition. Leader breaks goals into tasks, delegates to members, loops until complete.
```python
team = Team(
    members=[researcher, analyst, writer],
    mode="tasks",
    max_iterations=10,
)
# Leader creates task list, assigns to members, tracks completion
```

## Key Methods

```python
# Synchronous
response = team.run("Your message")
team.print_response("Your message", stream=True)

# Asynchronous
response = await team.arun("Your message")
await team.aprint_response("Your message", stream=True)
```

## Nested Teams

Teams can contain other teams as members:

```python
research_team = Team(
    name="Research Team",
    members=[web_agent, arxiv_agent],
    mode="broadcast",
)

analysis_team = Team(
    name="Analysis Team",
    members=[data_agent, viz_agent],
    mode="coordinate",
)

main_team = Team(
    name="Main Team",
    members=[research_team, analysis_team],
    mode="coordinate",
)
```

## Example: Investment Research Team

```python
from agno.agent import Agent
from agno.team.team import Team
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools

bull = Agent(
    name="Bull Analyst",
    role="Make the investment case FOR a stock",
    model=Gemini(id="gemini-3-flash-preview"),
    tools=[YFinanceTools()],
)

bear = Agent(
    name="Bear Analyst",
    role="Make the investment case AGAINST a stock",
    model=Gemini(id="gemini-3-flash-preview"),
    tools=[YFinanceTools()],
)

team = Team(
    name="Investment Research",
    model=Gemini(id="gemini-3-flash-preview"),
    members=[bull, bear],
    mode="broadcast",
    show_members_responses=True,
    markdown=True,
)

team.print_response("Should I invest in NVIDIA?", stream=True)
```
