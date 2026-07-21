# Tools Reference

## Creating Custom Tools

### Using the @tool Decorator

```python
from agno.tools.decorator import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name to get weather for.
    """
    # Your implementation
    return f"Weather in {city}: 72F, sunny"

agent = Agent(tools=[get_weather])
```

### Async Tools

```python
@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

### Decorator Options

```python
@tool(
    name="custom_name",                # Override function name
    description="Custom description",  # Override docstring
    show_result=True,                  # Show result to user
    stop_after_tool_call=True,         # Stop agent after this tool
    requires_confirmation=True,        # Ask user before executing
    cache_results=True,                # Cache results
    cache_ttl=3600,                    # Cache TTL in seconds
)
def my_tool(arg: str) -> str:
    """Docstring used as description if not overridden."""
    return "result"
```

### Tool Hooks

Hook parameters are injected by name — only `agent`, `team`, `run_context`, and `fc` (the `FunctionCall`) are recognized. A hook with any other signature raises a TypeError that agno swallows: the hook silently never runs.

```python
from agno.tools import FunctionCall, tool

def pre_hook(fc: FunctionCall):
    print(f"Calling {fc.function.name} with {fc.arguments}")

def post_hook(fc: FunctionCall):
    print(f"Result: {fc.result}")

@tool(pre_hook=pre_hook, post_hook=post_hook)
def my_tool(arg: str) -> str:
    return "result"
```

## Creating Toolkit Classes

For related tools, extend Toolkit:

```python
from agno.tools.toolkit import Toolkit

class MyToolkit(Toolkit):
    def __init__(self, api_key: str):
        super().__init__(name="my_toolkit")
        self.api_key = api_key
        self.register(self.search)
        self.register(self.get_details)

    def search(self, query: str) -> str:
        """Search for items."""
        return f"Results for {query}"

    def get_details(self, item_id: str) -> str:
        """Get details for an item."""
        return f"Details for {item_id}"

agent = Agent(tools=[MyToolkit(api_key="...")])
```

## Built-in Tools (120+)

### Search & Web
| Tool | Import | Description |
|------|--------|-------------|
| DuckDuckGoTools | `agno.tools.duckduckgo` | Web search via DuckDuckGo |
| TavilyTools | `agno.tools.tavily` | AI-optimized web search |
| BraveSearchTools | `agno.tools.bravesearch` | Brave search API |
| ExaTools | `agno.tools.exa` | Exa search API |
| SearxngTools | `agno.tools.searxng` | SearxNG metasearch |
| SerperTools | `agno.tools.serper` | Google SERP API |
| JinaReaderTools | `agno.tools.jina` | Jina AI tools |
| WebSearchTools | `agno.tools.websearch` | Generic web search |

### Data & Databases
| Tool | Import | Description |
|------|--------|-------------|
| DuckDbTools | `agno.tools.duckdb` | DuckDB SQL queries |
| PostgresTools | `agno.tools.postgres` | PostgreSQL queries |
| SQLTools | `agno.tools.sql` | Generic SQL tools |
| PandasTools | `agno.tools.pandas` | DataFrame operations |
| CsvTools | `agno.tools.csv_toolkit` | CSV file operations |

### Content & Knowledge
| Tool | Import | Description |
|------|--------|-------------|
| WikipediaTools | `agno.tools.wikipedia` | Wikipedia search |
| ArxivTools | `agno.tools.arxiv` | Academic paper search |
| PubmedTools | `agno.tools.pubmed` | Medical literature |
| HackerNewsTools | `agno.tools.hackernews` | HN stories/comments |
| NewspaperTools | `agno.tools.newspaper` | News article extraction |

### APIs & Integrations
| Tool | Import | Description |
|------|--------|-------------|
| GithubTools | `agno.tools.github` | GitHub API |
| JiraTools | `agno.tools.jira` | Jira project management |
| SlackTools | `agno.tools.slack` | Slack messaging |
| GmailTools | `agno.tools.gmail` | Gmail operations |
| NotionTools | `agno.tools.notion` | Notion pages/databases |
| LinearTools | `agno.tools.linear` | Linear issue tracking |
| DiscordTools | `agno.tools.discord` | Discord messaging |
| TelegramTools | `agno.tools.telegram` | Telegram bot |

### AI & Media
| Tool | Import | Description |
|------|--------|-------------|
| DalleTools | `agno.tools.dalle` | DALL-E image generation |
| ElevenLabsTools | `agno.tools.eleven_labs` | Text-to-speech |
| FalTools | `agno.tools.fal` | Fal.ai models |
| ReplicateTools | `agno.tools.replicate` | Replicate models |

### Finance
| Tool | Import | Description |
|------|--------|-------------|
| YFinanceTools | `agno.tools.yfinance` | Yahoo Finance data |
| OpenBBTools | `agno.tools.openbb` | Financial data platform |

### System & Files
| Tool | Import | Description |
|------|--------|-------------|
| ShellTools | `agno.tools.shell` | Shell command execution |
| FileTools | `agno.tools.file` | File read/write operations |
| PythonTools | `agno.tools.python` | Python code execution |

### MCP
| Tool | Import | Description |
|------|--------|-------------|
| MCPTools | `agno.tools.mcp` | Single MCP server |
| MultiMCPTools | `agno.tools.mcp` | Multiple MCP servers |
| MCPToolbox | `agno.tools.mcp_toolbox` | Toolbox MCP servers |

## Using Tools with Agents

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools

# Multiple toolkits
agent = Agent(
    tools=[
        DuckDuckGoTools(),
        YFinanceTools(),
        get_weather,  # Custom @tool function
    ],
    tool_call_limit=20,
)
```
