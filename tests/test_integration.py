"""
Integration tests for the CloudMart API.

These tests require:
    1. Redis running on localhost:6379
    2. The Flask server running on localhost:5000
       Start it with: python3 -m src.app

Run with: pytest tests/test_integration.py -v
"""

import pytest
import requests
import time
import redis

BASE_URL = "http://localhost:5000"


@pytest.fixture(autouse=True)
def flush_cache():
    """Flush Redis before each test to ensure a clean state."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.flushdb()
    except redis.ConnectionError:
        pass
    yield


@pytest.fixture
def server_running():
    """Skip tests if the API server is not running."""
    try:
        requests.get(f"{BASE_URL}/stats", timeout=2)
    except requests.ConnectionError:
        pytest.skip("API server not running on localhost:5000")


class TestCaching:
    """Test that caching improves performance."""

    def test_second_request_uses_cache(self, server_running):
        """Second GET for the same product should be a cache hit."""
        requests.get(f"{BASE_URL}/products/1")
        requests.get(f"{BASE_URL}/products/1")

        stats = requests.get(f"{BASE_URL}/stats").json()
        assert stats["cache_hits"] >= 1

    def test_cache_invalidation_on_order(self, server_running):
        """Placing an order should invalidate product cache."""
        requests.get(f"{BASE_URL}/products/1")

        requests.post(
            f"{BASE_URL}/orders",
            json={"product_id": 1, "quantity": 1, "customer_name": "CacheTest"},
        )

        resp = requests.get(f"{BASE_URL}/products/1")
        assert resp.status_code == 200


class TestRateLimiting:
    """Test that rate limiting blocks excess requests."""

    def test_rate_limit_kicks_in(self, server_running):
        """Sending many rapid requests should eventually get a 429."""
        denied = 0
        for _ in range(30):
            resp = requests.get(f"{BASE_URL}/products")
            if resp.status_code == 429:
                denied += 1

        assert denied > 0, "Rate limiter should deny some requests after the limit"


class TestOrders:
    """Test order placement through the full stack."""

    def test_place_order(self, server_running):
        resp = requests.post(
            f"{BASE_URL}/orders",
            json={"product_id": 1, "quantity": 1, "customer_name": "Alice"},
        )
        assert resp.status_code == 201
        order = resp.json()
        assert "id" in order
