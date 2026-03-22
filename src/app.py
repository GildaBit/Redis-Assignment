"""
CloudMart API Server.

This is the main Flask application for the CloudMart product catalog.
It exposes REST API endpoints for browsing products, placing orders,
and viewing system statistics.

Students must integrate three Redis backed layers into this application:
    1. Database Query Caching   (src/cache.py)
    2. Rate Limiting            (src/rate_limiter.py)
    3. Message Queuing / PubSub (src/message_broker.py)

Files that are GIVEN (do not modify):
    src/database.py
    src/performance.py

Files with TODOs (you must implement):
    src/cache.py
    src/rate_limiter.py
    src/message_broker.py
    src/app.py          (this file: complete the TODO sections below)
    src/worker.py
"""

from flask import Flask, jsonify, request
import time
import redis

from src.database import Database
from src.cache import CacheManager
from src.rate_limiter import RateLimiter
from src.message_broker import MessageBroker

app = Flask(__name__)

# ---- Initialize Components ----

database = Database()
cache = CacheManager()

_redis_client = None
try:
    _redis_client = redis.Redis(
        host="localhost", port=6379, db=0, decode_responses=True
    )
    _redis_client.ping()
except redis.ConnectionError:
    _redis_client = None

rate_limiter = RateLimiter(
    redis_client=_redis_client, max_requests=20, window_seconds=60
)
broker = MessageBroker(redis_client=_redis_client)

ORDER_QUEUE = "cloudmart:orders"
ORDER_CHANNEL = "cloudmart:order_events"

stats = {
    "cache_hits": 0,
    "cache_misses": 0,
    "requests_total": 0,
    "requests_rate_limited": 0,
    "orders_queued": 0,
}


# ---- Middleware ----


@app.before_request
def before_each_request():
    """
    Runs before every incoming request.

    Check the rate limiter and reject over-limit requests with HTTP 429.
    Include rate-limit info in the response headers.
    """
    request.start_time = time.time()
    stats["requests_total"] += 1

    # Implement rate limiting check here
    if rate_limiter.enabled:
        client_id = f"{request.remote_addr}:{request.method}:{request.path}"  # Use client IP as identifier
        allowed, info = rate_limiter.is_allowed(client_id) # Check if the request is allowed
        # Add rate limit info to response headers
        request.rate_limit_info = info  # Store info for after_request to add to headers
        if not allowed:
            stats["requests_rate_limited"] += 1
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after": info["reset_in"],
            }), 429
        


@app.after_request
def after_each_request(response):
    """Add latency header to every response."""
    if hasattr(request, "start_time"):
        latency_ms = (time.time() - request.start_time) * 1000
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
    return response


# ---- Product Endpoints ----


@app.route("/products", methods=["GET"])
def list_products():
    """
    List all products, with optional category filter.

    GET /products
    GET /products?category=Electronics

    Add caching to this endpoint. Track cache hits/misses in stats.
    """

    # get category filter from query parameters
    category = request.args.get("category")

    # Gets the cache key based on category if provided
    cache_key = f"products:category:{category}" if category else "products:all"
    result = cache.get(cache_key)
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        stats["cache_misses"] += 1

    if category:
        products = database.get_products_by_category(category)
    else:
        products = database.get_all_products()
    
    # Cache the result before returning on miss
    cache.set(cache_key, products)
    return jsonify(products)


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """
    Get a single product by ID.

    GET /products/1

    Add caching to this endpoint. Track cache hits/misses in stats.
    Do not cache 404 responses.
    """
    # Check cache first
    cache_key = f"product:{product_id}"
    result = cache.get(cache_key) # will return None if not found
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        # otherwise it's a cache miss
        stats["cache_misses"] += 1

    # Find the product in the database
    product = database.get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Cache the result before returning
    cache.set(cache_key, product)

    return jsonify(product)


@app.route("/products/search", methods=["GET"])
def search_products():
    """
    Search products by name or description.

    GET /products/search?q=laptop

    Add caching to this endpoint. Track cache hits/misses in stats.
    """
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    # Check cache first
    cache_key = f"products:search:{q}"
    result = cache.get(cache_key) # check if search query is in cache
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        stats["cache_misses"] += 1

    products = database.search_products(q)

    # Cache the result
    cache.set(cache_key, products)

    return jsonify(products)


@app.route("/products/top", methods=["GET"])
def top_products():
    """
    Get top rated products.

    GET /products/top
    GET /products/top?limit=5

    Add caching to this endpoint. Track cache hits/misses in stats.
    """
    limit = request.args.get("limit", 10, type=int)

    # Check cache first
    cache_key = f"products:top:{limit}" 
    result = cache.get(cache_key) # check if top products query is in cache
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        stats["cache_misses"] += 1

    products = database.get_top_rated(limit=limit)

    # Cache the result
    cache.set(cache_key, products)

    return jsonify(products)


@app.route("/products/price-range", methods=["GET"])
def products_by_price():
    """
    Get products within a price range.

    GET /products/price-range?min=10&max=50

    Add caching to this endpoint. Track cache hits/misses in stats.
    """
    min_price = request.args.get("min", type=float)
    max_price = request.args.get("max", type=float)

    if min_price is None or max_price is None:
        return jsonify(
            {"error": "Both 'min' and 'max' query parameters are required"}
        ), 400

    # Check cache first
    cache_key = f"products:price-range:{min_price}:{max_price}"
    result = cache.get(cache_key) # check if price range query is in cache
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        stats["cache_misses"] += 1

    products = database.get_products_by_price_range(min_price, max_price)

    # Cache the result
    cache.set(cache_key, products)

    return jsonify(products)


@app.route("/categories", methods=["GET"])
def list_categories():
    """
    List all product categories.

    GET /categories

    Add caching to this endpoint. Track cache hits/misses in stats.
    """
    #  Check cache first
    cache_key = "categories:all"
    result = cache.get(cache_key) # check if categories list is in cache
    if result is not None:
        stats["cache_hits"] += 1
        return jsonify(result) # Return cached result if available
    else:
        stats["cache_misses"] += 1

    categories = database.get_categories()

    # Cache the result
    cache.set(cache_key, categories)

    return jsonify(categories)


# ---- Order Endpoints ----


@app.route("/orders", methods=["POST"])
def place_order():
    """
    Place a new order.

    POST /orders
    Body: {"product_id": 1, "quantity": 2, "customer_name": "Alice"}

    After creating the order, enqueue it for background processing,
    publish an event, update stats, and invalidate affected caches.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    required_fields = ["product_id", "quantity", "customer_name"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    order = database.create_order(
        product_id=data["product_id"],
        quantity=data["quantity"],
        customer_name=data["customer_name"],
    )

    if order is None:
        return jsonify(
            {"error": "Could not create order. Product may not exist or insufficient stock."}
        ), 400

    # Enqueue order, publish event, update stats, invalidate caches
    broker.enqueue(ORDER_QUEUE, order) # Add order to processing queue
    broker.publish(ORDER_CHANNEL, order) # Publish event to notify listeners
    stats["orders_queued"] += 1
    cache.delete(f"product:{order['product_id']}") # Invalidate product cache since stock may have changed

    return jsonify(order), 201


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    """Get order details by ID."""
    order = database.get_order(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


@app.route("/queue/length", methods=["GET"])
def queue_length():
    """Get the current length of the order processing queue."""
    length = broker.queue_length(ORDER_QUEUE)
    return jsonify({"queue": ORDER_QUEUE, "length": length})


# ---- Stats Endpoint ----


@app.route("/stats", methods=["GET"])
def get_stats():
    """Return performance and cache statistics."""
    total_cache = stats["cache_hits"] + stats["cache_misses"]
    hit_rate = (stats["cache_hits"] / total_cache * 100) if total_cache > 0 else 0.0

    return jsonify(
        {
            "cache_hits": stats["cache_hits"],
            "cache_misses": stats["cache_misses"],
            "cache_hit_rate": round(hit_rate, 2),
            "requests_total": stats["requests_total"],
            "requests_rate_limited": stats["requests_rate_limited"],
            "orders_queued": stats["orders_queued"],
            "cache_enabled": cache.is_available(),
            "rate_limiter_enabled": rate_limiter.enabled,
            "message_broker_enabled": broker.enabled,
        }
    )


if __name__ == "__main__":
    print("CloudMart API Server starting...")
    print(f"  Cache enabled:          {cache.is_available()}")
    print(f"  Rate limiter enabled:   {rate_limiter.enabled}")
    print(f"  Message broker enabled: {broker.enabled}")
    print()
    app.run(debug=True, host="0.0.0.0", port=5000)
