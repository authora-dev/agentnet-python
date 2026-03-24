"""Billing resource -- balance, packages, purchase."""

from __future__ import annotations
from typing import Any


class BillingResource:
    def __init__(self, http):
        self._http = http

    def balance(self) -> dict[str, Any]:
        """Get current account balance, held amount, and total charged."""
        return self._http.get("/account/credits")

    def packages(self) -> list[dict[str, Any]]:
        """List available credit packages for purchase."""
        data = self._http.get("/account/credits")
        return data.get("packages", [])

    def purchase(self, package_id: str) -> dict[str, Any]:
        """Purchase a credit package."""
        return self._http.post("/account/credits/purchase", body={"packageId": package_id})


class AsyncBillingResource:
    def __init__(self, http):
        self._http = http

    async def balance(self) -> dict[str, Any]:
        return await self._http.get("/account/credits")

    async def packages(self) -> list[dict[str, Any]]:
        data = await self._http.get("/account/credits")
        return data.get("packages", [])

    async def purchase(self, package_id: str) -> dict[str, Any]:
        return await self._http.post("/account/credits/purchase", body={"packageId": package_id})
