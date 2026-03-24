"""Webhooks resource -- register, list, delete webhook endpoints."""

from __future__ import annotations
from typing import Any


class WebhooksResource:
    def __init__(self, http):
        self._http = http

    def register(self, url: str, events: list[str], secret: str | None = None) -> dict[str, Any]:
        """Register a webhook for task events."""
        body: dict[str, Any] = {"url": url, "events": events}
        if secret:
            body["secret"] = secret
        return self._http.post("/webhooks", body=body)

    def list(self) -> list[dict[str, Any]]:
        """List registered webhooks."""
        result = self._http.get("/webhooks")
        return result if isinstance(result, list) else result.get("items", [])

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook."""
        self._http.delete(f"/webhooks/{webhook_id}")


class AsyncWebhooksResource:
    def __init__(self, http):
        self._http = http

    async def register(self, url: str, events: list[str], secret: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"url": url, "events": events}
        if secret:
            body["secret"] = secret
        return await self._http.post("/webhooks", body=body)

    async def list(self) -> list[dict[str, Any]]:
        result = await self._http.get("/webhooks")
        return result if isinstance(result, list) else result.get("items", [])

    async def delete(self, webhook_id: str) -> None:
        await self._http.delete(f"/webhooks/{webhook_id}")
