"""
Tests for the RateLimiter class (src/rate_limiter.py).

These tests verify that your rate limiter correctly counts requests,
enforces limits, resets after the window, and handles disabled state.
Redis must be running on localhost:6379 for most tests.
"""

import pytest
import time
import redis


class TestRateLimiter:
    """Tests for RateLimiter."""

    def setup_method(self):
        try:
            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=1, decode_responses=True
            )
            self.redis_client.ping()
            self.redis_client.flushdb()
        except redis.ConnectionError:
            pytest.skip("Redis not available")

        from src.rate_limiter import RateLimiter

        self.limiter = RateLimiter(
            redis_client=self.redis_client, max_requests=5, window_seconds=10
        )

    def teardown_method(self):
        if hasattr(self, "redis_client"):
            self.redis_client.flushdb()

    def test_allows_requests_under_limit(self):
        """Requests within the limit should all be allowed."""
        for i in range(5):
            allowed, info = self.limiter.is_allowed("test_client_1")
            assert allowed is True, f"Request {i + 1} should be allowed"
            assert info["remaining"] == 5 - (i + 1)

    def test_blocks_requests_over_limit(self):
        """The request exceeding the limit should be blocked."""
        for _ in range(5):
            self.limiter.is_allowed("test_client_2")

        allowed, info = self.limiter.is_allowed("test_client_2")
        assert allowed is False
        assert info["remaining"] == 0

    def test_separate_clients_have_separate_limits(self):
        """Different clients should have independent counters."""
        for _ in range(5):
            self.limiter.is_allowed("client_a")

        allowed, info = self.limiter.is_allowed("client_b")
        assert allowed is True
        assert info["remaining"] == 4

    def test_limit_resets_after_window(self):
        """After the window expires, the limit should reset."""
        from src.rate_limiter import RateLimiter

        short_limiter = RateLimiter(
            redis_client=self.redis_client, max_requests=2, window_seconds=2
        )

        short_limiter.is_allowed("reset_client")
        short_limiter.is_allowed("reset_client")

        allowed, _ = short_limiter.is_allowed("reset_client")
        assert allowed is False

        time.sleep(3)

        allowed, info = short_limiter.is_allowed("reset_client")
        assert allowed is True

    def test_info_dict_has_required_fields(self):
        """The info dict should contain limit, remaining, reset_in, current_count."""
        allowed, info = self.limiter.is_allowed("info_client")
        assert "limit" in info
        assert "remaining" in info
        assert "reset_in" in info
        assert "current_count" in info

    def test_disabled_limiter_allows_all(self):
        """A limiter with no Redis should allow every request."""
        from src.rate_limiter import RateLimiter

        disabled = RateLimiter(redis_client=None, max_requests=1, window_seconds=1)

        for _ in range(100):
            allowed, _ = disabled.is_allowed("any_client")
            assert allowed is True

    def test_get_usage(self):
        """get_usage should reflect current usage without incrementing."""
        self.limiter.is_allowed("usage_client")
        self.limiter.is_allowed("usage_client")

        usage = self.limiter.get_usage("usage_client")
        assert usage["current_count"] == 2
        assert usage["remaining"] == 3
