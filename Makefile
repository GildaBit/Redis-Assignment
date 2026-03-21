.PHONY: help install test run worker perf clean verify redis-start redis-stop

help:
	@echo "CS496 Caching for Performance Assignment"
	@echo ""
	@echo "  make install       Install Python dependencies"
	@echo "  make redis-start   Start Redis via Docker Compose"
	@echo "  make redis-stop    Stop Redis"
	@echo "  make run           Start the Flask API server"
	@echo "  make worker        Start the order processing worker"
	@echo "  make test          Run unit tests (Redis must be running)"
	@echo "  make test-int      Run integration tests (server + Redis)"
	@echo "  make perf          Run performance benchmarks (server + Redis)"
	@echo "  make clean         Remove generated files"
	@echo "  make verify        Verify submission structure"

install:
	python3 -m pip install -r requirements.txt

redis-start:
	docker compose up -d

redis-stop:
	docker compose down

run:
	python3 -m src.app

worker:
	python3 -m src.worker

test:
	python3 -m pytest tests/test_cache.py tests/test_rate_limiter.py tests/test_message_broker.py -v

test-int:
	python3 -m pytest tests/test_integration.py -v

perf:
	python3 -m src.performance

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage cloudmart.db

verify:
	@echo "Checking required files..."
	@test -f src/cache.py && echo "  src/cache.py         OK" || echo "  src/cache.py         MISSING"
	@test -f src/rate_limiter.py && echo "  src/rate_limiter.py  OK" || echo "  src/rate_limiter.py  MISSING"
	@test -f src/message_broker.py && echo "  src/message_broker.py OK" || echo "  src/message_broker.py MISSING"
	@test -f src/app.py && echo "  src/app.py           OK" || echo "  src/app.py           MISSING"
	@test -f src/worker.py && echo "  src/worker.py        OK" || echo "  src/worker.py        MISSING"
	@test -f requirements.txt && echo "  requirements.txt     OK" || echo "  requirements.txt     MISSING"
	@test -f README.md && echo "  README.md            OK" || echo "  README.md            MISSING"
	@echo "Verification complete."
