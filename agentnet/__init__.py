"""AgentNet Python SDK -- AI engineering work as a service."""

from __future__ import annotations

from typing import Any

from ._http import SyncHttpClient, AsyncHttpClient
from .errors import (
    AgentNetError,
    AuthenticationError,
    AuthorizationError,
    InsufficientFundsError,
    NetworkError,
    NoWorkersError,
    NotFoundError,
    RateLimitError,
    TaskError,
    TimeoutError,
)
from .resources.tasks import TasksResource, AsyncTasksResource

__version__ = "0.1.6"
__all__ = [
    "__version__",
    "AgentNetClient",
    "AsyncAgentNetClient",
    "AgentNetError",
    "AuthenticationError",
    "AuthorizationError",
    "InsufficientFundsError",
    "NetworkError",
    "NoWorkersError",
    "NotFoundError",
    "RateLimitError",
    "TaskError",
    "TimeoutError",
]

DEFAULT_BASE_URL = "https://net.authora.dev/api/v1"


class AgentNetClient:
    """Synchronous AgentNet client.

    Example::

        from agentnet import AgentNetClient

        client = AgentNetClient(api_key="ank_live_...")
        result = client.tasks.submit_and_wait(skill="code-review", input="eval(x)")
        print(result["output"])
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 30):
        if not api_key:
            raise ValueError("api_key is required")
        self._http = SyncHttpClient(base_url, api_key, timeout)
        self.tasks = TasksResource(self._http)

    def quote(self, skill: str, region: str | None = None, priority: str = "standard") -> dict[str, Any]:
        """Get a price quote and worker availability."""
        body: dict[str, Any] = {"skillId": skill, "slaTier": priority}
        if region:
            body["region"] = region
        return self._http.post("/tasks/quote", body=body)

    def skills(self) -> list[dict[str, Any]]:
        """List available skills."""
        result = self._http.get("/registry/skills")
        return result if isinstance(result, list) else result.get("items", [])

    def balance(self) -> dict[str, Any]:
        """Get account balance."""
        return self._http.get("/account/credits")


class AsyncAgentNetClient:
    """Async AgentNet client (requires aiohttp).

    Example::

        from agentnet import AsyncAgentNetClient

        client = AsyncAgentNetClient(api_key="ank_live_...")
        result = await client.tasks.submit_and_wait(skill="code-review", input="eval(x)")
        print(result["output"])
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 30):
        if not api_key:
            raise ValueError("api_key is required")
        self._http = AsyncHttpClient(base_url, api_key, timeout)
        self.tasks = AsyncTasksResource(self._http)

    async def quote(self, skill: str, region: str | None = None, priority: str = "standard") -> dict[str, Any]:
        body: dict[str, Any] = {"skillId": skill, "slaTier": priority}
        if region:
            body["region"] = region
        return await self._http.post("/tasks/quote", body=body)

    async def skills(self) -> list[dict[str, Any]]:
        result = await self._http.get("/registry/skills")
        return result if isinstance(result, list) else result.get("items", [])

    async def balance(self) -> dict[str, Any]:
        return await self._http.get("/account/credits")

    async def close(self):
        await self._http.close()
