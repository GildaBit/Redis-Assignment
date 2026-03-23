# CS496 Caching for Performance
## Name: Gilad Bitton
## RedID: 130621085

<!-- Fill in this README as part of your submission. See ASSIGNMENT.md for the full assignment details. -->

## How to Run

<!-- Explain how to install dependencies, start Redis, run the server, and run the worker. -->

1. **Install dependencies**
```bash
make install
```
2. **Start Redis (using Docker)**
```bash
make redis-start
```
3. **Run the Flask applications**
```bash
make run
```
4. **Run the worker (in a separate terminal)**
```bash
make worker
```
5. **Run tests (in third terminal)**
```bash
make test
```
6. **Run performance tests**
```bash
make perf
```

## What I Implemented

<!-- Describe what you built in each file and any design decisions you made. -->

*cache.py*
- Implemented a Redis backed cache with the ability to:
     - get
     - set
     - delete
     - flush
- Used JSON serialization to store them as Python dicts
- Used TTL with the setex function to automatically have expirations for cached data
- Implemented a fallback fro when Redis is unavailable

*rate_limiter.py*
- Implemented a rate limiter using Redis:
     - used INCR to count requests
     - used EXPIRE to define the time window
- Each client is tracked using:
  client_id = f"{IP}:{method}:{path}"
- Returns metadata including the amount of remaining requests and time until reset
- Fails open if Redis is unavailable

*message_broker*
- Implemented:
     - Queue system using Redis prebuilt lists
          - Using RPUSH and BLPOP
     - Pub/Sub system using Redis channels
- Supports enqueueing orders and events

*app.py*
- Added caching to multiple endpoints:
     - /products
     - /products/top
     - /products/search
     - /products/price-range
- Cached keys are structured consistently
     E.g. products:category:Electronics
- Implemented cache hitt/miss tracking
- Added rate limiting use the before_request function
- Implemented cache invalidation when orders are placed

*worker.py*
- Continuously processes orders from the queue
- Listens for events via Redis Pub/Sub implemented in message_broker
- Simulates order processing

## Performance Test Results

<!-- Paste the output of `make perf` and briefly discuss what you observe.
     How much faster are cache hits compared to cache misses? -->

### Results:

CloudMart Performance Tests
Server: http://localhost:5000

============================================================
TEST 1: LATENCY COMPARISON (Cached vs Uncached)
============================================================

Cache flushed. Starting with an empty cache.

Request  1 (expected CACHE MISS):   54.31 ms  [status 200]
Requests 2..20 (expected CACHE HITS): avg 3.41 ms

Speedup from caching: 15.9x faster

Individual cache hit latencies (ms):
  Request  2:   2.64 ms  ##
  Request  3:   2.20 ms  ##
  Request  4:   2.64 ms  ##
  Request  5:   2.29 ms  ##
  Request  6:   2.23 ms  ##
  Request  7:   2.83 ms  ##
  Request  8:   2.67 ms  ##
  Request  9:   2.57 ms  ##
  Request 10:   3.12 ms  ###
  Request 11:  18.87 ms  ##################
  Request 12:   2.69 ms  ##
  Request 13:   2.36 ms  ##
  Request 14:   2.49 ms  ##
  Request 15:   2.37 ms  ##
  Request 16:   2.67 ms  ##
  Request 17:   2.86 ms  ##
  Request 18:   2.44 ms  ##
  Request 19:   2.53 ms  ##
  Request 20:   2.38 ms  ##

Cache miss latency:        54.31 ms
Average cache hit latency: 3.41 ms
Min cache hit latency:     2.20 ms
Max cache hit latency:     18.87 ms

============================================================
TEST 2: CATEGORY QUERY CACHING
============================================================

First request  (MISS):   53.52 ms  [status 200]
Second request (HIT):     2.62 ms
Speedup: 20.5x

============================================================
TEST 3: RATE LIMITING
============================================================

Sending 30 rapid requests to http://localhost:5000/products...

  Request  1: OK     (200)  53.88 ms
  Request  2: OK     (200)  3.71 ms
  Request  3: OK     (200)  2.87 ms
  Request  4: OK     (200)  3.25 ms
  Request  5: OK     (200)  3.64 ms
  Request  6: OK     (200)  3.37 ms
  Request  7: OK     (200)  3.28 ms
  Request  8: OK     (200)  3.46 ms
  Request  9: OK     (200)  3.39 ms
  Request 10: OK     (200)  3.74 ms
  Request 11: OK     (200)  3.17 ms
  Request 12: OK     (200)  3.43 ms
  Request 13: OK     (200)  3.75 ms
  Request 14: OK     (200)  3.34 ms
  Request 15: OK     (200)  2.48 ms
  Request 16: OK     (200)  2.57 ms
  Request 17: OK     (200)  2.94 ms
  Request 18: OK     (200)  2.60 ms
  Request 19: DENIED (429)  2.53 ms
  Request 20: DENIED (429)  2.12 ms
  Request 21: DENIED (429)  1.97 ms
  Request 22: DENIED (429)  2.35 ms
  Request 23: DENIED (429)  2.13 ms
  Request 24: DENIED (429)  2.01 ms
  Request 25: DENIED (429)  2.84 ms
  Request 26: DENIED (429)  2.20 ms
  Request 27: DENIED (429)  2.14 ms
  Request 28: DENIED (429)  2.46 ms
  Request 29: DENIED (429)  2.34 ms
  Request 30: DENIED (429)  2.19 ms

Results: 18 allowed, 12 denied

============================================================
TEST 4: MESSAGE QUEUE (Order Processing)
============================================================

Placing 5 test orders...
  Order 1: status 201, latency 71.57 ms
  Order 2: status 201, latency 65.99 ms
  Order 3: status 201, latency 66.05 ms
  Order 4: status 201, latency 65.65 ms
  Order 5: status 201, latency 66.57 ms

Queue length: 4

============================================================
SERVER STATISTICS
============================================================

  cache_enabled: True
  cache_hit_rate: 92.5
  cache_hits: 37
  cache_misses: 3
  message_broker_enabled: True
  orders_queued: 5
  rate_limiter_enabled: True
  requests_rate_limited: 12
  requests_total: 60


All performance tests completed.

### Observations:

- Caching provides major speed improvement
     - Cache miss: ~54 ms
     - Cache hit: ~ 3.4 ms
     - Improvement: ~15-20x faster
- Category Queries show similar improvement
     - First request: ~53 ms
     - Second request: ~2.6 ms
     - Improvement: ~20x faster
- Rate limiting works as intended
     - 30 rapid requests were sent
     - 18 were allowed, 12 were denied
     - Demonstrates enforcement of request limits