# Bug Fixes

## Bug 1 — api/main.py line 8: Hardcoded localhost for Redis host
Problem: redis.Redis(host="localhost") fails inside Docker containers because localhost refers to the container itself, not the Redis service.
Fix: Replaced with os.getenv("REDIS_HOST", "localhost") so the host is configurable via environment variable.

## Bug 2 — api/main.py line 8: Redis password never used
Problem: The .env file defined REDIS_PASSWORD but the Redis connection never passed it, so authentication always failed in production.
Fix: Added password=os.getenv("REDIS_PASSWORD", None) to the Redis connection.

## Bug 3 — api/main.py line 8: Redis port hardcoded
Problem: Port 6379 was hardcoded, making it impossible to change without modifying source code.
Fix: Replaced with int(os.getenv("REDIS_PORT", "6379")).

## Bug 4 — api/main.py line 22: Queue key hardcoded as "job"
Problem: The queue key was hardcoded as "job" with no way to configure it via environment variables.
Fix: Replaced with os.getenv("QUEUE_KEY", "jobs") defined at module level.

## Bug 5 — api/main.py line 28: 404 returned as HTTP 200
Problem: return {"error": "not found"} sends HTTP 200 with an error body. The frontend received it as a success and crashed trying to render undefined status.
Fix: Replaced with raise HTTPException(status_code=404, detail="Job not found").

## Bug 6 — api/main.py: Missing HTTPException import
Problem: HTTPException was used but never imported, causing a NameError on startup.
Fix: Added HTTPException to the FastAPI import line.

## Bug 7 — api/main.py: No /health endpoint
Problem: No health check endpoint existed, making Docker HEALTHCHECK and depends_on: condition: service_healthy impossible.
Fix: Added GET /health endpoint that pings Redis and returns 200 or 503.

## Bug 8 — api/main.py: Missing blank lines between functions
Problem: flake8 reported E302 expected 2 blank lines between function definitions, violating PEP8.
Fix: Added two blank lines between all top-level function definitions.

## Bug 9 — worker/worker.py line 6: Hardcoded localhost for Redis host
Problem: Same as Bug 1 — localhost fails inside Docker containers.
Fix: Replaced with os.getenv("REDIS_HOST", "localhost").

## Bug 10 — worker/worker.py line 6: Redis password never used
Problem: Same as Bug 2 — password from environment was ignored.
Fix: Added password=os.getenv("REDIS_PASSWORD", None) to the Redis connection.

## Bug 11 — worker/worker.py line 4: signal imported but never used
Problem: import signal was present but no handlers were registered. A SIGTERM from Docker would kill the worker mid-job, leaving that job stuck as queued forever.
Fix: Implemented SIGTERM and SIGINT handlers that set a shutdown flag, changed while True to while not shutdown.

## Bug 12 — worker/worker.py: sys imported but never used
Problem: flake8 reported F401 sys imported but unused, failing the lint stage.
Fix: Removed import sys.

## Bug 13 — worker/worker.py: No error handling on Redis disconnect
Problem: If Redis became temporarily unavailable, an unhandled ConnectionError would crash the worker permanently with no recovery.
Fix: Wrapped the loop body in try/except redis.exceptions.ConnectionError with a 5-second retry delay.

## Bug 14 — worker/worker.py: Queue key hardcoded as "job"
Problem: Queue key was hardcoded and did not match the configurable key from the API side.
Fix: Replaced with os.getenv("QUEUE_KEY", "jobs").

## Bug 15 — worker/worker.py: No newline at end of file
Problem: flake8 reported W292 no newline at end of file, violating PEP8.
Fix: Added a newline at the end of the file.

## Bug 16 — frontend/app.js line 6: Hardcoded localhost:8000 for API URL
Problem: const API_URL = "http://localhost:8000" fails inside Docker because containers cannot reach each other via localhost.
Fix: Replaced with process.env.API_URL || 'http://localhost:8000'.

## Bug 17 — frontend/app.js: All upstream errors collapsed to 500
Problem: Both catch blocks always returned HTTP 500 regardless of the actual upstream error.
Fix: Added const status = err.response ? err.response.status : 500 in both catch blocks.

## Bug 18 — frontend/app.js: No /health endpoint
Problem: No health check endpoint existed for Docker HEALTHCHECK instruction.
Fix: Added GET /health route returning { status: ok }.

## Bug 19 — api/.env: Secret file committed to git
Problem: REDIS_PASSWORD was committed to the repository, exposing credentials to anyone who clones the repo.
Fix: Removed from git tracking with git rm --cached api/.env, added to .gitignore, created .env.example with placeholder values.

## Bug 20 — requirements.txt: No pinned versions
Problem: Dependencies had no pinned versions, making builds non-reproducible.
Fix: Pinned all dependencies to exact versions in both api/requirements.txt and worker/requirements.txt.
