"""
Tests for the MessageBroker class (src/message_broker.py).

These tests cover both the message queue (Redis Lists) and the
pub/sub functionality. Redis must be running on localhost:6379.
"""

import pytest
import time
import redis


class TestMessageQueue:
    """Tests for message queue (Redis Lists) functionality."""

    def setup_method(self):
        try:
            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=2, decode_responses=True
            )
            self.redis_client.ping()
            self.redis_client.flushdb()
        except redis.ConnectionError:
            pytest.skip("Redis not available")

        from src.message_broker import MessageBroker

        self.broker = MessageBroker(redis_client=self.redis_client)

    def teardown_method(self):
        if hasattr(self, "redis_client"):
            self.redis_client.flushdb()

    def test_enqueue_message(self):
        """Adding a message to the queue should succeed."""
        result = self.broker.enqueue("test:queue", {"order_id": 1, "item": "widget"})
        assert result is True

    def test_dequeue_message(self):
        """Dequeue should return the message that was enqueued."""
        self.broker.enqueue("test:queue", {"order_id": 42})

        message = self.broker.dequeue("test:queue", timeout=1)
        assert message is not None
        assert message["order_id"] == 42

    def test_fifo_order(self):
        """Messages should be dequeued in the order they were enqueued."""
        for i in range(3):
            self.broker.enqueue("test:fifo", {"seq": i})

        for i in range(3):
            msg = self.broker.dequeue("test:fifo", timeout=1)
            assert msg is not None
            assert msg["seq"] == i

    def test_dequeue_empty_returns_none(self):
        """Dequeue on an empty queue should return None after timeout."""
        msg = self.broker.dequeue("test:empty", timeout=1)
        assert msg is None

    def test_queue_length(self):
        """queue_length should reflect the current number of messages."""
        assert self.broker.queue_length("test:len") == 0

        self.broker.enqueue("test:len", {"a": 1})
        self.broker.enqueue("test:len", {"b": 2})
        assert self.broker.queue_length("test:len") == 2

        self.broker.dequeue("test:len", timeout=1)
        assert self.broker.queue_length("test:len") == 1

    def test_disabled_broker(self):
        """A broker with no Redis should handle calls gracefully."""
        from src.message_broker import MessageBroker

        disabled = MessageBroker(redis_client=None)

        assert disabled.enqueue("q", {"x": 1}) is False
        assert disabled.dequeue("q", timeout=1) is None
        assert disabled.queue_length("q") == 0


class TestPubSub:
    """Tests for pub/sub functionality."""

    def setup_method(self):
        try:
            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=2, decode_responses=True
            )
            self.redis_client.ping()
            self.redis_client.flushdb()
        except redis.ConnectionError:
            pytest.skip("Redis not available")

        from src.message_broker import MessageBroker

        self.publisher = MessageBroker(redis_client=self.redis_client)

        self.sub_redis = redis.Redis(
            host="localhost", port=6379, db=2, decode_responses=True
        )
        self.subscriber = MessageBroker(redis_client=self.sub_redis)

    def teardown_method(self):
        if hasattr(self, "subscriber"):
            self.subscriber.unsubscribe()
        if hasattr(self, "redis_client"):
            self.redis_client.flushdb()

    def test_subscribe_returns_pubsub(self):
        """Subscribing should return a PubSub object."""
        ps = self.subscriber.subscribe("test:channel")
        assert ps is not None

    def test_publish_and_receive(self):
        """A published message should be received by a subscriber."""
        self.subscriber.subscribe("test:events")
        time.sleep(0.5)

        self.publisher.publish("test:events", {"event": "test", "value": 123})
        time.sleep(0.5)

        msg = self.subscriber.get_message(timeout=2.0)
        assert msg is not None
        assert msg["event"] == "test"
        assert msg["value"] == 123

    def test_publish_returns_subscriber_count(self):
        """publish() should return the number of subscribers that received it."""
        self.subscriber.subscribe("test:count_channel")
        time.sleep(0.5)

        count = self.publisher.publish("test:count_channel", {"data": "hello"})
        assert count >= 1

    def test_unsubscribe(self):
        """Unsubscribing should set pubsub back to None."""
        self.subscriber.subscribe("test:unsub")
        self.subscriber.unsubscribe()
        assert self.subscriber.pubsub is None
