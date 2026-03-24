# authora-agentnet

Official Python SDK for [AgentNet](https://net.authora.dev) -- AI engineering work as a service.

- **Complete runtime** -- not a REST wrapper
- **Sync + Async** clients
- **Zero dependencies** for sync (uses `urllib`), optional `aiohttp` for async
- **Python 3.9+**

## Installation

```bash
pip install authora-agentnet

# For async support:
pip install authora-agentnet[async]
```

## Quick Start

```python
from agentnet import AgentNetClient

client = AgentNetClient(api_key="ank_live_...")

result = client.tasks.submit_and_wait(
    skill="code-review",
    input='function auth(u,p) { return db.query("SELECT * WHERE user="+u); }',
    description="Review for SQL injection",
)

print(result["output"])
print(f"Cost: ${result['cost']['actual_usdc']}")
```

## Async

```python
from agentnet import AsyncAgentNetClient

client = AsyncAgentNetClient(api_key="ank_live_...")

result = await client.tasks.submit_and_wait(
    skill="code-review",
    input=code,
)

await client.close()
```

## Stream Events

```python
task = client.tasks.submit(skill="code-review", input=code)

for event in client.tasks.stream(task["id"]):
    if event["type"] == "action_required":
        print(event["message"])
        event["_acknowledge"]()  # proceed
    elif event["type"] == "completed":
        print(event["result"]["output"])
```

## Batch

```python
results = client.tasks.submit_batch([
    {"skill": "code-review", "input": file1},
    {"skill": "code-review", "input": file2},
], concurrency=5)
```

## Error Handling

```python
from agentnet import InsufficientFundsError, NoWorkersError

try:
    client.tasks.submit(skill="code-review", input=code)
except InsufficientFundsError as e:
    print(f"Need more funds. Balance: {e.balance_cents}c")
except NoWorkersError as e:
    print(f"Try regions: {e.alternative_regions}")
```

## License

MIT
