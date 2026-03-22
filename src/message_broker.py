"""
Redis based Message Broker for CloudMart.

Students must implement the MessageBroker class which provides two
messaging capabilities built on Redis:

1. Message Queue (Redis Lists): Reliable, first in first out delivery
   of messages between a producer and one or more worker consumers.
   Used here to queue orders for background processing.

2. Pub/Sub (Redis Publish/Subscribe): Broadcast event notifications
   to any number of listeners in real time. Used here to announce
   events like "order placed" so that multiple services can react.

"""

import redis
import json
from typing import Optional, Any


class MessageBroker:
    """
    Provides message queue and pub/sub capabilities using Redis.

    Attributes:
        redis_client: The redis.Redis connection, or None.
        enabled: True when Redis is connected and messaging is available.
        pubsub: A redis.client.PubSub object for subscriptions, or None.
    """

    def __init__(self, redis_client: redis.Redis = None):
        """
        Initialize the MessageBroker.

        Set self.enabled based on whether redis_client is available.

        Args:
            redis_client: An active redis.Redis connection, or None.
        """
        self.redis_client = redis_client
        self.enabled = False
        self.pubsub = None

        # Set self.enabled based on whether redis_client is available
        try:
            self.redis_client.ping()  # Test connection
            self.enabled = True
        except Exception:
            self.enabled = False       

    # ----------------------------------------------------------------
    # Message Queue Methods (using Redis Lists)
    # ----------------------------------------------------------------

    def enqueue(self, queue_name: str, message: dict) -> bool:
        """
        Add a message to the end of a queue.

        Serialize and append the message to the queue.

        Args:
            queue_name: The Redis list key used as the queue.
            message: A dict representing the message payload.

        Returns:
            True if the message was added to the queue, False otherwise.
        """
        # Implement message enqueue
        added = False
        if not self.enabled:
            return added
        try:
            # Serialize the message dict to a JSON string and push it to the Redis list
            self.redis_client.rpush(queue_name, json.dumps(message))
            added = True
        except redis.RedisError:
            added = False
        return added

    def dequeue(self, queue_name: str, timeout: int = 1) -> Optional[dict]:
        """
        Remove and return the oldest message from the front of a queue.

        Wait for and return the next message from the front of the queue.
        Use a blocking approach so the caller waits efficiently.

        Args:
            queue_name: The Redis list key used as the queue.
            timeout: How many seconds to wait for a message (0 = forever).

        Returns:
            The message dict, or None if no message within the timeout.
        """
        # Implement message dequeue
        if not self.enabled:
            return None
        try:
            # Use BLPOP from Redis to block until a message is available or timeout occurs
            message = self.redis_client.blpop(queue_name, timeout=timeout)
            if message:
                # message is a tuple (queue_name, message_json)
                return json.loads(message[1])  # Deserialize JSON string to dict
        except redis.RedisError:
            pass
        return None

    def queue_length(self, queue_name: str) -> int:
        """
        Get the number of messages waiting in a queue.

        Return the number of messages waiting in the queue.

        Args:
            queue_name: The Redis list key used as the queue.

        Returns:
            The number of messages in the queue.
        """
        # Implement queue length check
        if not self.enabled:
            return 0
        try:
            return self.redis_client.llen(queue_name)
        except redis.RedisError:
            pass            
        return 0

    # ----------------------------------------------------------------
    # Pub/Sub Methods
    # ----------------------------------------------------------------

    def publish(self, channel: str, message: dict) -> int:
        """
        Publish a message to a channel.

        Serialize and broadcast the message to all channel subscribers.

        Args:
            channel: The pub/sub channel name.
            message: The dict to broadcast to subscribers.

        Returns:
            The number of subscribers that received the message.
        """
        # Implement pub/sub publish
        if not self.enabled:
            return 0
        try:
            return self.redis_client.publish(channel, json.dumps(message))
        except redis.RedisError:
            pass
        return 0

    def subscribe(self, channel: str):
        """
        Subscribe to a channel and return the PubSub object.

        Create a subscription to the given channel.
        Drain the initial confirmation message before returning.

        Args:
            channel: The channel name to subscribe to.

        Returns:
            The PubSub object for listening, or None on error.
        """
        # Implement pub/sub subscribe
        if not self.enabled:
            return None
        try:
            # Create a PubSub object and subscribe to the channel
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(channel)
            self.pubsub.get_message(timeout=1)  # Wait for the subscription confirmation
            return self.pubsub
        except redis.RedisError:
            pass
        return None

    def get_message(self, timeout: float = 1.0) -> Optional[dict]:
        """
        Get the next message from a subscribed channel.

        Poll for the next data message from the subscription.

        Args:
            timeout: How many seconds to wait for a message.

        Returns:
            The message dict, or None if nothing available.
        """
        # Implement getting messages from subscription
        if not self.enabled:
            return None
        if self.pubsub:
            try:
                # Use the PubSub object to get the next message, waiting up to the timeout
                message = self.pubsub.get_message(timeout=timeout)
                # The message dict will have a 'type' field; we only want 'message' types which contain data
                if message and message['type'] == 'message':
                    return json.loads(message['data'])  # Deserialize JSON string to dict
            except redis.RedisError:
                pass
        return None

    def unsubscribe(self):
        """
        Unsubscribe from all channels and clean up resources.

        Clean up the pub/sub subscription and release resources.
        """
        # Implement unsubscribe and cleanup
        if not self.enabled:
            return
        if self.pubsub:
            try:
                self.pubsub.unsubscribe()  # Unsubscribe from all channels
                self.pubsub.close()        # Close the PubSub connection
            except redis.RedisError:
                pass
            finally:
                self.pubsub = None
        
