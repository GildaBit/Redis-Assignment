"""
Performance measurement utilities for CloudMart.

THIS FILE IS GIVEN. Do not modify it.

Run this script after implementing your caching, rate limiting, and
message broker code to see how each layer affects system performance.

Usage:
    python3 -m src.performance

The API server must be running on localhost:5000 before you run this.
"""

import requests
import time
import statistics

BASE_URL = "http://localhost:5000"


def measure_request(method: str, url: str, **kwargs):
    """Make an HTTP request and return (status_code, latency_ms)."""
    start = time.time()
    response = requests.request(method, url, **kwargs)
    latency_ms = (time.time() - start) * 1000
    return response.status_code, latency_ms


def run_latency_comparison():
    """Compare latency for cached vs uncached product requests."""
    print("=" * 60)
    print("TEST 1: LATENCY COMPARISON (Cached vs Uncached)")
    print("=" * 60)

    endpoint = f"{BASE_URL}/products/1"

    try:
        import redis as r

        rc = r.Redis(host="localhost", port=6379, db=0)
        rc.flushdb()
        print("\nCache flushed. Starting with an empty cache.\n")
    except Exception:
        print("\nCould not flush cache. Results may vary.\n")

    status, first_latency = measure_request("GET", endpoint)
    print(f"Request  1 (expected CACHE MISS): {first_latency:7.2f} ms  [status {status}]")

    hit_latencies = []
    for _ in range(19):
        status, latency = measure_request("GET", endpoint)
        hit_latencies.append(latency)

    avg_hit = statistics.mean(hit_latencies)
    print(f"Requests 2..20 (expected CACHE HITS): avg {avg_hit:.2f} ms\n")

    if avg_hit > 0:
        speedup = first_latency / avg_hit
        print(f"Speedup from caching: {speedup:.1f}x faster")

    print("\nIndividual cache hit latencies (ms):")
    for i, lat in enumerate(hit_latencies, start=2):
        bar = "#" * max(1, int(lat))
        print(f"  Request {i:2d}: {lat:6.2f} ms  {bar}")

    print(f"\nCache miss latency:        {first_latency:.2f} ms")
    print(f"Average cache hit latency: {avg_hit:.2f} ms")
    print(f"Min cache hit latency:     {min(hit_latencies):.2f} ms")
    print(f"Max cache hit latency:     {max(hit_latencies):.2f} ms")


def run_category_cache_test():
    """Test caching for category queries."""
    print("\n" + "=" * 60)
    print("TEST 2: CATEGORY QUERY CACHING")
    print("=" * 60)

    endpoint = f"{BASE_URL}/products?category=Electronics"

    try:
        import redis as r

        rc = r.Redis(host="localhost", port=6379, db=0)
        rc.flushdb()
    except Exception:
        pass

    status, miss_latency = measure_request("GET", endpoint)
    print(f"\nFirst request  (MISS): {miss_latency:7.2f} ms  [status {status}]")

    _, hit_latency = measure_request("GET", endpoint)
    print(f"Second request (HIT):  {hit_latency:7.2f} ms")

    if hit_latency > 0:
        print(f"Speedup: {miss_latency / hit_latency:.1f}x")


def run_rate_limit_test():
    """Send rapid requests to trigger rate limiting."""
    print("\n" + "=" * 60)
    print("TEST 3: RATE LIMITING")
    print("=" * 60)

    endpoint = f"{BASE_URL}/products"
    allowed = 0
    denied = 0

    print(f"\nSending 30 rapid requests to {endpoint}...\n")

    for i in range(30):
        status, latency = measure_request("GET", endpoint)
        if status == 429:
            denied += 1
            print(f"  Request {i + 1:2d}: DENIED (429)  {latency:.2f} ms")
        else:
            allowed += 1
            print(f"  Request {i + 1:2d}: OK     ({status})  {latency:.2f} ms")

    print(f"\nResults: {allowed} allowed, {denied} denied")
    if denied == 0:
        print("NOTE: No requests were denied. Is rate limiting implemented?")


def run_queue_test():
    """Place orders and verify they enter the queue."""
    print("\n" + "=" * 60)
    print("TEST 4: MESSAGE QUEUE (Order Processing)")
    print("=" * 60)

    print("\nPlacing 5 test orders...")
    for i in range(5):
        order_data = {
            "product_id": i + 1,
            "quantity": 1,
            "customer_name": f"TestCustomer{i + 1}",
        }
        status, latency = measure_request(
            "POST", f"{BASE_URL}/orders", json=order_data
        )
        print(f"  Order {i + 1}: status {status}, latency {latency:.2f} ms")

    resp = requests.get(f"{BASE_URL}/queue/length")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\nQueue length: {data.get('length', 'unknown')}")
    else:
        print(f"\nQueue length endpoint returned status {resp.status_code}")


def run_stats_check():
    """Print the current server statistics."""
    print("\n" + "=" * 60)
    print("SERVER STATISTICS")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print()
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  Error: status {response.status_code}")
    except requests.ConnectionError:
        print("  Could not connect to server.")


if __name__ == "__main__":
    print("CloudMart Performance Tests")
    print(f"Server: {BASE_URL}")
    print()

    try:
        requests.get(f"{BASE_URL}/stats", timeout=2)
    except requests.ConnectionError:
        print("ERROR: Cannot connect to the API server.")
        print("Start the server first: python3 -m src.app")
        exit(1)

    run_latency_comparison()
    run_category_cache_test()
    run_rate_limit_test()
    run_queue_test()
    run_stats_check()

    print("\n\nAll performance tests completed.")
