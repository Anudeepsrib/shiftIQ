# Programmatic invocation

Set `LANGSMITH_FLEET_API_URL`, `LANGSMITH_FLEET_AGENT_ID`, and `LANGGRAPH_API_KEY` (or `LANGSMITH_API_KEY`). Then:

```python
import asyncio
from code_migration.fleet.client import ShiftIQFleetClient

result = asyncio.run(
    ShiftIQFleetClient().analyze_repository("owner/repository", "react-hooks")
)
```

The client calls the documented stateless Agent Server endpoint `POST /runs/wait` with `X-Api-Key` and `X-Auth-Scheme: langsmith-api-key`. It exposes only a safe analysis helper; destructive retries are intentionally absent.

For the official LangGraph SDK, install `langgraph-sdk`, create `get_client(url=..., api_key=..., headers={"X-Auth-Scheme": "langsmith-api-key"})`, then call `client.runs.wait(None, agent_id, input={"messages": [...]})`.
