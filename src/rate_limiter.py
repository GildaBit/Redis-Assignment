"""
Redis based Rate Limiter for CloudMart API.

Students must implement the RateLimiter class to control the frequency
of API requests using Redis as the tracking backend.

Rate limiting prevents any single client from overwhelming the server
with too many requests. Each client (identified by IP address or API key)
is allowed a certain number of requests within a fixed time window.
Redis is used to atomically count requests and expire counters.

TODO: Implement all methods marked with TODO.
"""

import redis
from typing import Tuple


class RateLimiter:
    """
    Fixed window rate limiter backed by Redis.

    For each client, a Redis key tracks how many requests have been made
    in the current time window. The key automatically expires at the end
    of the window, resetting the counter for the next window.

    Attributes:
        redis_client: The redis.Redis connection, or None.
        max_requests: Maximum requests allowed per window.
        window_seconds: Duration of each rate limit window in seconds.
        enabled: True when Redis is connected and rate limiting is active.
    """

    def __init__(
        self,
        redis_client: redis.Redis = None,
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        """
        Initialize the RateLimiter.

        TODO: Set self.enabled based on whether redis_client is available.

        Args:
            redis_client: An active redis.Redis connection, or None.
            max_requests: Maximum number of requests allowed per window.
            window_seconds: Duration of the rate limit window in seconds.
        """
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = False

        # TODO: Set self.enabled based on whether redis_client is available

    def is_allowed(self, client_id: str) -> Tuple[bool, dict]:
        """
        Check whether a client is allowed to make a request.

        TODO: Implement fixed-window rate limiting.
        Track per-client request counts and deny when over the limit.
        Fail open (allow all requests) if Redis is unavailable.

        Args:
            client_id: A unique identifier for the client (e.g., IP address).

        Returns:
            A tuple (is_allowed, info) where is_allowed is a bool and info
            is a dict with keys: limit, remaining, reset_in, current_count.
        """
        info = {
            "limit": self.max_requests,
            "remaining": self.max_requests,
            "reset_in": self.window_seconds,
            "current_count": 0,
        }

        # TODO: Implement rate limiting logic

        return (True, info)

    def get_usage(self, client_id: str) -> dict:
        """
        Get the current rate limit usage for a client without incrementing.

        TODO: Read current usage for a client without incrementing.

        Args:
            client_id: The client identifier.

        Returns:
            A dict with rate limit usage information.
        """
        # TODO: Implement usage lookup
        return {
            "limit": self.max_requests,
            "remaining": self.max_requests,
            "reset_in": self.window_seconds,
            "current_count": 0,
        }
