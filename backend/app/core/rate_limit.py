"""A small in-process rate limiter for the AI-calling endpoints.

The Gemini endpoints cost money and are the obvious abuse target, so each user gets a fixed number
of AI requests per rolling minute. This is per-process (fine for a single-instance MVP); a
multi-instance deployment would move this to a shared store like Redis.
"""

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record a request for `key` and return whether it is within the limit."""
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()
