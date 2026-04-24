# FIXES.md — Bug Fixes Documentation

This document details every bug found in the starter repository, the file and line it was found on, what the problem was, and exactly what was changed to fix it.

---

## Bug 1 — api/main.py: Hardcoded Redis host

**File:** `api/main.py`
**Line:** 8

**Problem:**
The Redis connection used `localhost` as the host. Inside Docker containers, `localhost` refers to the container itself, not the Redis service. This means the API could never connect to Redis when running in Docker.

**Before:**
```python
r = redis.Redis(host="localhost", port=6379)
```

**After:**
```python
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
```

**Why:** Docker services communicate via service names (e.g. `redis`), not `localhost`. Reading from environment variables makes the host configurable for both local and containerised environments.

---

## Bug 2 — api/main.py: Redis password never used

**File:** `api/main.py`
**Line:** 8

**Problem:**
The `.env` file defined `REDIS_PASSWORD` but the Redis connection never passed it. Redis authentication always failed silently in production.

**Before:**
```python
r = redis.Redis(host="localhost", port=6379)
```

**After:**
```python
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
```

**Why:** Without passing the password, any Redis instance configured with `requirepass` would reject all connections.

---

## Bug 3 — api/main.py: Missing HTTPException import

**File:** `api/main.py`
**Line:** 1

**Problem:**
`HTTPException` was used in the health and job routes but was never imported. The application would crash immediately on startup with a `NameError`.

**Before:**
```python
from fastapi import FastAPI
```

**After:**
```python
from fastapi import FastAPI, HTTPException
```

**Why:** Python raises `NameError: name 'HTTPException' is not defined` at runtime if a name is used without being imported.

---

## Bug 4 — api/main.py: Queue key hardcoded as "job"

**File:** `api/main.py`
**Line:** 22

**Problem:**
The queue key was hardcoded as the string `"job"`. This made it impossible to change without modifying source code, and created a risk of mismatch between the API and worker if either was updated independently.

**Before:**
```python
r.lpush("job", job_id)
```

**After:**
```python
QUEUE_KEY = os.getenv("QUEUE_KEY", "jobs")
r.lpush(QUEUE_KEY, job_id)
```

**Why:** Both the API and worker must use the same queue key. Making it an environment variable ensures they stay in sync and allows configuration without code changes.

---

## Bug 5 — api/main.py: Job not found returned as HTTP 200

**File:** `api/main.py`
**Line:** 28

**Problem:**
When a job was not found, the route returned `{"error": "not found"}` with an HTTP 200 status code. The frontend received this as a successful response and tried to render `data.status` which was `undefined`, causing the UI to break silently.

**Before:**
```python
if not status:
    return {"error": "not found"}
```

**After:**
```python
if not status:
    raise HTTPException(status_code=404, detail="Job not found")
```

**Why:** HTTP status codes must accurately reflect the result. A 404 tells the client the resource does not exist, allowing it to handle the error correctly.

---

## Bug 6 — api/main.py: No /health endpoint

**File:** `api/main.py`

**Problem:**
There was no `/health` endpoint. Without one, Docker's `HEALTHCHECK` instruction cannot probe the API, and `depends_on: condition: service_healthy` in docker-compose cannot work. Services would start before the API was ready.

**Before:**
No health endpoint existed.

**After:**
```python
@app.get("/health")
def health():
    try:
        r.ping()
        return {"status": "ok"}
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
```

**Why:** Health checks are required for production-grade container orchestration. The endpoint also verifies Redis connectivity, not just that the process is running.

---

## Bug 7 — api/main.py: Missing blank lines between functions (PEP8)

**File:** `api/main.py`
**Lines:** 15, 22, 30

**Problem:**
flake8 reported `E302 expected 2 blank lines` between top-level function definitions. This violated PEP8 and failed the lint stage of the CI pipeline.

**Before:**
```python
    return {"job_id": job_id}
@app.get("/health")
def health():
```

**After:**
```python
    return {"job_id": job_id}


@app.get("/health")
def health():
```

**Why:** PEP8 requires two blank lines between top-level definitions. This is enforced by flake8 in the lint stage.

---

## Bug 8 — worker/worker.py: Hardcoded Redis host

**File:** `worker/worker.py`
**Line:** 6

**Problem:**
Same as Bug 1. The worker connected to Redis using `localhost`, which fails inside Docker containers.

**Before:**
```python
r = redis.Redis(host="localhost", port=6379)
```

**After:**
```python
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
```

**Why:** Same reason as Bug 1 — containers must use service names, not localhost.

---

## Bug 9 — worker/worker.py: signal imported but never used

**File:** `worker/worker.py`
**Line:** 4

**Problem:**
`import signal` was present in the original code but no signal handlers were ever registered. This meant the worker had no graceful shutdown. When Docker sent a `SIGTERM` to stop the container, the worker would be killed immediately, potentially mid-job, leaving that job stuck in `queued` status forever.

**Before:**
```python
import signal
# signal was never used
while True:
    job = r.brpop("job", timeout=5)
```

**After:**
```python
import signal

shutdown = False

def handle_signal(signum, frame):
    global shutdown
    shutdown = True

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

while not shutdown:
    job = r.brpop(QUEUE_KEY, timeout=5)
```

**Why:** Graceful shutdown ensures the worker finishes its current job before exiting. Without it, jobs get permanently stuck.

---

## Bug 10 — worker/worker.py: sys imported but never used

**File:** `worker/worker.py`
**Line:** 5

**Problem:**
`import sys` was present but never used anywhere in the file. flake8 reported `F401 'sys' imported but unused`, which failed the lint stage.

**Before:**
```python
import sys
```

**After:**
Removed entirely.

**Why:** Unused imports add noise, can confuse readers, and fail linting rules.

---

## Bug 11 — worker/worker.py: No error handling on Redis disconnect

**File:** `worker/worker.py`

**Problem:**
The worker loop had no error handling. If Redis became temporarily unavailable (restart, network blip), an unhandled `ConnectionError` would crash the worker process permanently. It would never recover without a manual restart.

**Before:**
```python
while True:
    job = r.brpop("job", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id.decode())
```

**After:**
```python
while not shutdown:
    try:
        job = r.brpop(QUEUE_KEY, timeout=5)
        if job:
            _, job_id = job
            process_job(job_id.decode())
    except redis.exceptions.ConnectionError:
        time.sleep(5)
```

**Why:** Production workers must be resilient to transient infrastructure failures. A retry loop with backoff allows the worker to recover automatically.

---

## Bug 12 — worker/worker.py: Queue key hardcoded as "job"

**File:** `worker/worker.py`

**Problem:**
Same as Bug 4. The worker popped from the hardcoded key `"job"` while the API needed to push to the same key. Any mismatch would silently break the queue.

**Before:**
```python
job = r.brpop("job", timeout=5)
```

**After:**
```python
QUEUE_KEY = os.getenv("QUEUE_KEY", "jobs")
job = r.brpop(QUEUE_KEY, timeout=5)
```

**Why:** Both services must use the same configurable key, controlled by environment variables.

---

## Bug 13 — worker/worker.py: No newline at end of file

**File:** `worker/worker.py`
**Line:** Last line

**Problem:**
flake8 reported `W292 no newline at end of file`. This violated PEP8 and failed the lint stage.

**Before:**
File ended without a trailing newline.

**After:**
Added a single newline at the end of the file.

**Why:** POSIX standard requires text files to end with a newline. flake8 enforces this.

---

## Bug 14 — frontend/app.js: Hardcoded API URL

**File:** `frontend/app.js`
**Line:** 6

**Problem:**
The API URL was hardcoded as `http://localhost:8000`. Inside Docker, the frontend container cannot reach the API via `localhost` — it must use the service name `api`.

**Before:**
```javascript
const API_URL = "http://localhost:8000";
```

**After:**
```javascript
const API_URL = process.env.API_URL || 'http://localhost:8000';
```

**Why:** Container-to-container communication uses Docker's internal DNS (service names). The URL must be injectable via environment variable.

---

## Bug 15 — frontend/app.js: All errors returned as HTTP 500

**File:** `frontend/app.js`
**Lines:** 18, 28

**Problem:**
Both catch blocks always returned HTTP 500 regardless of what error the API returned. A 404 from the API (job not found) was hidden from the browser as a 500, making debugging impossible.

**Before:**
```javascript
} catch (err) {
    res.status(500).json({ error: "something went wrong" });
}
```

**After:**
```javascript
} catch (err) {
    const status = err.response ? err.response.status : 500;
    res.status(status).json({ error: 'something went wrong' });
}
```

**Why:** Forwarding the correct HTTP status code allows the frontend to distinguish between different error types and handle them appropriately.

---

## Bug 16 — frontend/app.js: No /health endpoint

**File:** `frontend/app.js`

**Problem:**
No health check endpoint existed for the Docker `HEALTHCHECK` instruction or for `depends_on: condition: service_healthy` in docker-compose.

**Before:**
No health endpoint existed.

**After:**
```javascript
app.get('/health', (req, res) => res.json({ status: 'ok' }));
```

**Why:** Required for Docker health checks and service dependency ordering in docker-compose.

---

## Bug 17 — frontend/package.json: Missing lint and test scripts

**File:** `frontend/package.json`

**Problem:**
The `package.json` only had a `start` script. The CI pipeline requires `npm run lint` and `npm run test` to exist. Running either would fail with `Missing script` error.

**Before:**
```json
"scripts": {
    "start": "node app.js"
}
```

**After:**
```json
"scripts": {
    "start": "node app.js",
    "lint": "eslint app.js",
    "test": "jest --coverage --testPathPattern=tests/"
}
```

**Why:** CI pipelines require standardised script entry points. Without them the lint and test stages cannot run.

---

## Bug 18 — frontend: Missing .eslintrc.json

**File:** `frontend/.eslintrc.json` (missing)

**Problem:**
ESLint was listed as a dev dependency and `npm run lint` was added, but no ESLint configuration file existed. Running ESLint without a config file causes it to exit with an error.

**Before:**
No `.eslintrc.json` existed.

**After:**
```json
{
  "env": { "node": true, "es6": true },
  "extends": "eslint:recommended",
  "parserOptions": { "ecmaVersion": 2021 }
}
```

**Why:** ESLint requires a configuration file to know which rules to enforce and which environment globals are available.

---

## Bug 19 — api/.env: Secret file committed to git

**File:** `api/.env`

**Problem:**
The file `api/.env` containing `REDIS_PASSWORD=supersecretpassword123` was committed to the repository in the original starter code. Anyone who clones the repo has access to the credentials.

**Before:**
`api/.env` was tracked by git and visible in commit history.

**After:**
- Removed from git tracking: `git rm --cached api/.env`
- Added to `.gitignore`: `api/.env` and `.env`
- Created `.env.example` with placeholder values only

**Why:** Secrets must never be stored in version control. They should be passed via environment variables or a secrets manager at runtime.

---

## Bug 20 — requirements.txt: No pinned dependency versions

**File:** `api/requirements.txt`, `worker/requirements.txt`

**Problem:**
All dependencies were listed without version pins (e.g. just `fastapi` with no version). This makes builds non-reproducible — a new package release could silently introduce breaking changes or security vulnerabilities.

**Before:**