"""
Redis Cache Manager for CloudMart.

Students must implement the CacheManager class to provide
Redis backed caching for database query results.

When Redis is running, query results are stored with a time to live (TTL)
so that repeated queries return much faster. When Redis is unavailable,
the application must still work by falling back to direct database queries.

TODO: Implement all methods marked with TODO.
"""

import redis
import json
from typing import Optional, Any


class CacheManager:
    """
    Manages Redis backed caching for database query results.

    Attributes:
        host: Redis server hostname.
        port: Redis server port.
        db: Redis database number.
        default_ttl: Default time to live in seconds for cached entries.
        redis_client: The redis.Redis connection object, or None.
        enabled: True when Redis is connected and usable.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_ttl: int = 60,
    ):
        """
        Initialize the CacheManager and attempt to connect to Redis.

        Connect to Redis and set self.enabled on success.
        The app must still work if Redis is unavailable.

        Args:
            host: Redis server hostname (default 'localhost')
            port: Redis server port (default 6379)
            db: Redis database number (default 0)
            default_ttl: Default TTL in seconds for cached entries (default 60)
        """
        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = default_ttl
        self.redis_client = None
        self.enabled = False
        # Connect to Redis and set self.enabled accordingly
        try:
            seld.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            self.redis_client.ping() # Test connection
            self.enabled = True
        except redis.RedisError:
            print("Warning: Redis is unavailable. Caching is disabled.")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Retrieve and deserialize the cached value.
        Return None on miss or error.

        Args:
            key: The cache key to look up.

        Returns:
            The cached Python object, or None on miss or error.
        """
        if key is None:
            return None
        if not self.enabled:
            return None
        try:
            # Attempt to get the value from Redis
            value = self.redis_client.get(key)
            if value is not None:
                return json.loads(value) # Deserialize JSON string to Python object
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Store a value in the cache with a time to live.

        Serialize and store the value with a TTL.

        Args:
            key: The cache key.
            value: The Python object to cache (must be JSON serializable).
            ttl: Time to live in seconds. Uses default_ttl if not specified.

        Returns:
            True if the value was stored successfully, False otherwise.
        """
        # Implement cache storage
        if key is None or value is None:
            return False
        if not self.enabled:
            return False
        try:
            # Use default TTL if not provided
            ttl = self.default_ttl if ttl is None else ttl
            value_str = json.dumps(value) # Serialize Python object to JSON string
            self.redis_client.setex(key, ttl, value_str) # Store with TTL
            return True
        except (redis.RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Remove the key from Redis.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        # Implement cache deletion
        if key is None:
            return False
        if not self.enabled:
            return False
        try:
            # Attempt to delete the key from Redis
            result = self.redis_client.delete(key)
            return result > 0 # delete returns the number of keys deleted
        except redis.RedisError:
            return False

    def flush(self) -> bool:
        """
        Clear all entries from the current Redis database.

        Implement this method.

        Returns:
            True if the database was flushed, False otherwise.
        """
        # Implement cache flush
        if not self.enabled:
            return False
        try:
            self.redis_client.flushdb() # Clear all keys in the current database
            return True
        except redis.RedisError:
            return False

    def is_available(self) -> bool:
        """Return True if the Redis cache is connected and usable."""
        return self.enabled
