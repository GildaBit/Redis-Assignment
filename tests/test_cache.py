"""
Tests for the CacheManager class (src/cache.py).

These tests verify that your Redis cache implementation correctly
stores, retrieves, deletes, and expires cached values.
Redis must be running on localhost:6379 for most tests.
"""

import pytest
import time


class TestCacheManager:
    """Tests for CacheManager."""

    def setup_method(self):
        from src.cache import CacheManager

        self.cache = CacheManager()
        if self.cache.is_available():
            self.cache.flush()

    def test_cache_connects_to_redis(self):
        """CacheManager should report whether Redis is available."""
        from src.cache import CacheManager

        cm = CacheManager()
        assert isinstance(cm.enabled, bool)

    def test_set_and_get(self):
        """Storing a value and retrieving it should return the same data."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        result = self.cache.set("test:key1", {"name": "Widget", "price": 9.99})
        assert result is True

        value = self.cache.get("test:key1")
        assert value is not None
        assert value["name"] == "Widget"
        assert value["price"] == 9.99

    def test_get_nonexistent_key(self):
        """Getting a key that does not exist should return None."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        value = self.cache.get("test:nonexistent:key:abc123")
        assert value is None

    def test_delete(self):
        """Deleting a cached value should remove it from Redis."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        self.cache.set("test:delete_me", {"data": "temporary"})
        assert self.cache.get("test:delete_me") is not None

        result = self.cache.delete("test:delete_me")
        assert result is True
        assert self.cache.get("test:delete_me") is None

    def test_ttl_expiration(self):
        """A cached value should disappear after its TTL expires."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        self.cache.set("test:expiring", {"data": "short_lived"}, ttl=2)
        assert self.cache.get("test:expiring") is not None

        time.sleep(3)
        assert self.cache.get("test:expiring") is None

    def test_flush(self):
        """Flushing should remove all cached values."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        self.cache.set("test:flush1", "value1")
        self.cache.set("test:flush2", "value2")

        result = self.cache.flush()
        assert result is True
        assert self.cache.get("test:flush1") is None
        assert self.cache.get("test:flush2") is None

    def test_cache_stores_complex_objects(self):
        """Lists and nested dicts should survive serialization."""
        if not self.cache.is_available():
            pytest.skip("Redis not available")

        data = [
            {"id": 1, "name": "Product A", "tags": ["sale", "new"]},
            {"id": 2, "name": "Product B", "tags": ["popular"]},
        ]
        self.cache.set("test:complex", data)
        result = self.cache.get("test:complex")
        assert result == data

    def test_graceful_degradation(self):
        """CacheManager should handle an unreachable Redis gracefully."""
        from src.cache import CacheManager

        cm = CacheManager(host="localhost", port=9999)
        assert cm.is_available() is False
        assert cm.get("any_key") is None
        assert cm.set("any_key", "value") is False
        assert cm.delete("any_key") is False
