"""Deliverables resource -- list and download task output files."""

from __future__ import annotations
from typing import Any


class DeliverablesResource:
    def __init__(self, http):
        self._http = http

    def list(self, task_id: str) -> list[dict[str, Any]]:
        """List deliverables for a completed task."""
        data = self._http.get(f"/tasks/{task_id}/artifacts")
        return data.get("artifacts", [])

    def get_content(self, task_id: str, filename: str) -> str:
        """Get a specific deliverable's content by filename."""
        all_files = self.list(task_id)
        match = next((d for d in all_files if d.get("filename") == filename or d.get("path") == filename), None)
        if not match:
            raise ValueError(f'Deliverable "{filename}" not found for task {task_id}')
        if match.get("content"):
            return match["content"]
        if match.get("downloadUrl"):
            from urllib.request import urlopen
            with urlopen(match["downloadUrl"]) as resp:
                return resp.read().decode("utf-8")
        raise ValueError(f'Deliverable "{filename}" has no content or download URL')


class AsyncDeliverablesResource:
    def __init__(self, http):
        self._http = http

    async def list(self, task_id: str) -> list[dict[str, Any]]:
        data = await self._http.get(f"/tasks/{task_id}/artifacts")
        return data.get("artifacts", [])

    async def get_content(self, task_id: str, filename: str) -> str:
        all_files = await self.list(task_id)
        match = next((d for d in all_files if d.get("filename") == filename or d.get("path") == filename), None)
        if not match:
            raise ValueError(f'Deliverable "{filename}" not found for task {task_id}')
        if match.get("content"):
            return match["content"]
        raise ValueError(f'Deliverable "{filename}" has no content')
