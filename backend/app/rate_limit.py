
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException, Request


# In-memory limits for local development.
_request_times = {}
_request_lock = Lock()


def rate_limit(
    limit: int,
    window_seconds: int,
    scope: str
):
    async def check_rate_limit(request: Request):
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        key = (scope, client_ip)
        now = time.monotonic()
        cutoff = now - window_seconds

        with _request_lock:
            timestamps = _request_times.setdefault(
                key, deque()
            )

            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= limit:
                retry_after = max(
                    1,
                    int(window_seconds - (now - timestamps[0])) + 1
                )

                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)}
                )

            timestamps.append(now)

    return check_rate_limit
