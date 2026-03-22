"""
CloudMart Order Processing Worker.

This background process consumes orders from the Redis message queue
and processes them. It also subscribes to the order events channel
to demonstrate Pub/Sub functionality.

In production systems, worker processes run separately from the web
server. They pick up jobs from a queue and handle them asynchronously,
so the web server can respond to the user immediately without waiting
for slow tasks like payment processing or email sending to finish.

Students must complete the TODO sections in run_queue_worker()
and run_event_listener().
"""

import time
import threading
import redis

from src.message_broker import MessageBroker
from src.database import Database

ORDER_QUEUE = "cloudmart:orders"
ORDER_CHANNEL = "cloudmart:order_events"


def process_order(order: dict, database: Database) -> bool:
    """
    Process a single order from the queue.

    In a real system this might charge a payment method, reserve inventory,
    send a confirmation email, and update shipping records. Here we simulate
    that work with short delays and update the order status in the database.

    THIS FUNCTION IS GIVEN. Do not modify it.
    """
    order_id = order.get("id")
    if not order_id:
        print("  WARNING: Order missing 'id' field. Skipping.")
        return False

    print(f"  Processing order #{order_id}...")
    time.sleep(0.5) # simulate processing time

    database.update_order_status(order_id, "processing")
    time.sleep(0.5) # simulate processing time

    database.update_order_status(order_id, "completed")
    print(f"  Order #{order_id} completed.")
    return True


def run_queue_worker(broker: MessageBroker, database: Database):
    """
    Continuously consume orders from the message queue and process them.

    Continuously dequeue and process orders. Support graceful shutdown.
    """
    # queue consumer loop
    while True:
        try:
            order = broker.dequeue(ORDER_QUEUE, timeout=5) # Wait for an order with a timeout to allow graceful shutdown
            if order:
                process_order(order, database)
        except Exception as e:
            time.sleep(1) # Sleep briefly on error to avoid tight loop

    


def run_event_listener(broker: MessageBroker):
    """
    Subscribe to the order events channel and print events as they arrive.

    Subscribe to order events and print each one. Clean up on exit.
    """
    # event listener
    try:
        pubsub = broker.redis_client.pubsub()
        pubsub.subscribe(ORDER_CHANNEL)
        print(f"Subscribed to channel '{ORDER_CHANNEL}'")
        message = broker.get_message(pubsub, timeout=5) # Wait for messages with a timeout to allow graceful shutdown
        while message:
            if message["type"] == "message":
                event_data = message["data"]
                print(f"Received event on channel '{ORDER_CHANNEL}': {event_data}")
            message = broker.get_message(pubsub, timeout=5)
    except Exception as e:
        pass
    finally:
        broker.unsubscribe()


def main():
    """Start the worker and event listener."""
    print("=" * 50) # print a separator line with 50 equals signs
    print("CloudMart Order Processing Worker")
    print("=" * 50) # print a separator line with 50 equals signs

    try:
        redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True # connect to Redis on localhost:6379
        )
        redis_client.ping()
        print("Connected to Redis.")
    except redis.ConnectionError:
        print("ERROR: Cannot connect to Redis. Is Redis running?")
        print("Start Redis with: make redis-start  (or: redis-server)")
        return

    database = Database()
    broker = MessageBroker(redis_client=redis_client)

    listener_thread = threading.Thread(
        target=run_event_listener,
        args=(MessageBroker(redis_client=redis_client),),
        daemon=True,
    )
    listener_thread.start()

    run_queue_worker(broker, database)


if __name__ == "__main__":
    main()
