from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero")

        self._interval = 1.0 / requests_per_second
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_at

            delay = self._interval - elapsed

            if delay > 0:
                await asyncio.sleep(delay)

            self._last_request_at = time.monotonic()