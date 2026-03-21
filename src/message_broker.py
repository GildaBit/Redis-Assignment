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

TODO: Implement all methods marked with TODO.
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

        TODO: Set self.enabled based on whether redis_client is available.

        Args:
            redis_client: An active redis.Redis connection, or None.
        """
        self.redis_client = redis_client
        self.enabled = False
        self.pubsub = None

        # TODO: Set self.enabled based on redis_client availability

    # ----------------------------------------------------------------
    # Message Queue Methods (using Redis Lists)
    # ----------------------------------------------------------------

    def enqueue(self, queue_name: str, message: dict) -> bool:
        """
        Add a message to the end of a queue.

        TODO: Serialize and append the message to the queue.

        Args:
            queue_name: The Redis list key used as the queue.
            message: A dict representing the message payload.

        Returns:
            True if the message was added to the queue, False otherwise.
        """
        # TODO: Implement message enqueue
        return False

    def dequeue(self, queue_name: str, timeout: int = 1) -> Optional[dict]:
        """
        Remove and return the oldest message from the front of a queue.

        TODO: Wait for and return the next message from the front of the queue.
        Use a blocking approach so the caller waits efficiently.

        Args:
            queue_name: The Redis list key used as the queue.
            timeout: How many seconds to wait for a message (0 = forever).

        Returns:
            The message dict, or None if no message within the timeout.
        """
        # TODO: Implement message dequeue
        return None

    def queue_length(self, queue_name: str) -> int:
        """
        Get the number of messages waiting in a queue.

        TODO: Return the number of messages waiting in the queue.

        Args:
            queue_name: The Redis list key used as the queue.

        Returns:
            The number of messages in the queue.
        """
        # TODO: Implement queue length check
        return 0

    # ----------------------------------------------------------------
    # Pub/Sub Methods
    # ----------------------------------------------------------------

    def publish(self, channel: str, message: dict) -> int:
        """
        Publish a message to a channel.

        TODO: Serialize and broadcast the message to all channel subscribers.

        Args:
            channel: The pub/sub channel name.
            message: The dict to broadcast to subscribers.

        Returns:
            The number of subscribers that received the message.
        """
        # TODO: Implement pub/sub publish
        return 0

    def subscribe(self, channel: str):
        """
        Subscribe to a channel and return the PubSub object.

        TODO: Create a subscription to the given channel.
        Drain the initial confirmation message before returning.

        Args:
            channel: The channel name to subscribe to.

        Returns:
            The PubSub object for listening, or None on error.
        """
        # TODO: Implement pub/sub subscribe
        return None

    def get_message(self, timeout: float = 1.0) -> Optional[dict]:
        """
        Get the next message from a subscribed channel.

        TODO: Poll for the next data message from the subscription.

        Args:
            timeout: How many seconds to wait for a message.

        Returns:
            The message dict, or None if nothing available.
        """
        # TODO: Implement getting messages from subscription
        return None

    def unsubscribe(self):
        """
        Unsubscribe from all channels and clean up resources.

        TODO: Clean up the pub/sub subscription and release resources.
        """
        # TODO: Implement unsubscribe and cleanup
        pass
