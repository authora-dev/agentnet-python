"""Tasks resource -- submit, wait, stream, batch, cancel, retry."""

from __future__ import annotations

import time
from typing import Any, Iterator

from ..errors import TaskError, TimeoutError


class TasksResource:
    """Sync tasks resource."""

    def __init__(self, http):
        self._http = http

    def submit(self, *, skill: str, input: str, description: str = "", priority: str = "standard",
               region: str | None = None, min_trust_score: int | None = None) -> dict[str, Any]:
        """Submit a task for execution."""
        body = {"skillId": skill, "inputEncrypted": input, "description": description, "slaTier": priority}
        if region:
            body["region"] = region
        if min_trust_score is not None:
            body["minTrustScore"] = min_trust_score
        return self._http.post("/tasks", body=body)

    def get(self, task_id: str) -> dict[str, Any]:
        """Get task details."""
        return self._http.get(f"/tasks/{task_id}")

    def status(self, task_id: str) -> dict[str, Any]:
        """Get task status with customer events."""
        return self._http.get(f"/tasks/{task_id}/status")

    def cancel(self, task_id: str) -> None:
        """Cancel a task."""
        self._http.post(f"/tasks/{task_id}/cancel")

    def retry(self, task_id: str) -> dict[str, Any]:
        """Retry a failed task."""
        return self._http.post(f"/tasks/{task_id}/retry")

    def acknowledge(self, task_id: str) -> None:
        """Acknowledge an action_required event."""
        self._http.post(f"/tasks/{task_id}/acknowledge")

    def wait(self, task_id: str, timeout: int = 300, poll_interval: int = 3) -> dict[str, Any]:
        """Wait for task completion by polling."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = self.get(task_id)
            if task.get("status") == "completed":
                return self._build_result(task)
            if task.get("status") in ("failed", "cancelled"):
                raise TaskError(f"Task {task_id} {task['status']}", task_id, task["status"])
            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    def submit_and_wait(self, *, skill: str, input: str, description: str = "",
                        priority: str = "standard", timeout: int = 300, **kwargs) -> dict[str, Any]:
        """Submit a task and wait for completion."""
        task = self.submit(skill=skill, input=input, description=description, priority=priority, **kwargs)
        return self.wait(task["id"], timeout=timeout)

    def stream(self, task_id: str, poll_interval: int = 2) -> Iterator[dict[str, Any]]:
        """Stream task events. Yields event dicts with type, message, actions."""
        last_count = 0
        while True:
            data = self.status(task_id)
            events = data.get("customerEvents", [])
            for i in range(last_count, len(events)):
                evt = events[i]
                evt["_acknowledge"] = lambda: self.acknowledge(task_id)
                evt["_cancel"] = lambda: self.cancel(task_id)
                yield evt
            last_count = len(events)

            if data.get("status") == "completed":
                result = self._build_result(data)
                yield {"type": "completed", "message": "Task completed", "result": result}
                return
            if data.get("status") in ("failed", "cancelled"):
                yield {"type": "failed", "message": f"Task {data['status']}"}
                return
            time.sleep(poll_interval)

    def submit_batch(self, tasks: list[dict[str, Any]], concurrency: int = 5,
                     on_progress=None) -> dict[str, Any]:
        """Submit multiple tasks and wait for all. Returns results and failures."""
        import concurrent.futures

        results = []
        failed = []
        completed = 0

        def run_one(params):
            nonlocal completed
            try:
                result = self.submit_and_wait(**params)
                results.append(result)
            except Exception as e:
                failed.append({"params": params, "error": str(e)})
            finally:
                completed += 1
                if on_progress:
                    on_progress(completed, len(tasks))

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            pool.map(run_one, tasks)

        return {"results": results, "failed": failed}

    def _build_result(self, task: dict[str, Any]) -> dict[str, Any]:
        full = self._http.get(f"/tasks/{task['id']}")
        deliverables = []
        try:
            art_data = self._http.get(f"/tasks/{task['id']}/artifacts")
            deliverables = art_data.get("artifacts", [])
        except Exception:
            pass

        return {
            "id": task["id"],
            "status": task.get("status", "completed"),
            "output": full.get("outputEncrypted", ""),
            "cost": {
                "estimate_usdc": float(full.get("priceEstimateUsdc", 0)),
                "actual_usdc": float(full.get("actualCostUsdc", 0)),
            },
            "duration_seconds": full.get("durationSeconds", 0),
            "model": full.get("model"),
            "deliverables": deliverables,
        }


class AsyncTasksResource:
    """Async tasks resource."""

    def __init__(self, http):
        self._http = http

    async def submit(self, *, skill: str, input: str, description: str = "",
                     priority: str = "standard", **kwargs) -> dict[str, Any]:
        body = {"skillId": skill, "inputEncrypted": input, "description": description, "slaTier": priority}
        body.update(kwargs)
        return await self._http.post("/tasks", body=body)

    async def get(self, task_id: str) -> dict[str, Any]:
        return await self._http.get(f"/tasks/{task_id}")

    async def status(self, task_id: str) -> dict[str, Any]:
        return await self._http.get(f"/tasks/{task_id}/status")

    async def cancel(self, task_id: str) -> None:
        await self._http.post(f"/tasks/{task_id}/cancel")

    async def acknowledge(self, task_id: str) -> None:
        await self._http.post(f"/tasks/{task_id}/acknowledge")

    async def wait(self, task_id: str, timeout: int = 300, poll_interval: int = 3) -> dict[str, Any]:
        import asyncio
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = await self.get(task_id)
            if task.get("status") == "completed":
                return await self._build_result(task)
            if task.get("status") in ("failed", "cancelled"):
                raise TaskError(f"Task {task_id} {task['status']}", task_id, task["status"])
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    async def submit_and_wait(self, *, skill: str, input: str, timeout: int = 300, **kwargs) -> dict[str, Any]:
        task = await self.submit(skill=skill, input=input, **kwargs)
        return await self.wait(task["id"], timeout=timeout)

    async def _build_result(self, task: dict[str, Any]) -> dict[str, Any]:
        full = await self._http.get(f"/tasks/{task['id']}")
        deliverables = []
        try:
            art_data = await self._http.get(f"/tasks/{task['id']}/artifacts")
            deliverables = art_data.get("artifacts", [])
        except Exception:
            pass
        return {
            "id": task["id"],
            "status": task.get("status", "completed"),
            "output": full.get("outputEncrypted", ""),
            "cost": {"estimate_usdc": float(full.get("priceEstimateUsdc", 0)), "actual_usdc": float(full.get("actualCostUsdc", 0))},
            "duration_seconds": full.get("durationSeconds", 0),
            "model": full.get("model"),
            "deliverables": deliverables,
        }
