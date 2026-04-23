# HNG14 Stage 2 DevOps

A job processing system consisting of three services: a Node.js frontend, a Python/FastAPI backend, and a Python worker, connected via Redis.

## Prerequisites

- Docker
- Docker Compose plugin (`docker compose version`)
- Git

## Quick Start

### 1. Clone the repository

git clone https://github.com/RichardBenjamin/hng14-stage2-devops
cd hng14-stage2-devops

### 2. Create your .env file

cp .env.example .env

Edit .env and set a strong REDIS_PASSWORD.

### 3. Start the stack

docker compose up --build

### 4. Verify it is running

Open http://localhost:3000 in your browser. Click Submit New Job — the status should change from queued to completed within a few seconds.

## Services

| Service  | Description                   | Port          |
|----------|-------------------------------|---------------|
| frontend | Node.js/Express job dashboard | 3000          |
| api      | Python/FastAPI job manager    | 8000 internal |
| worker   | Python job processor          | none          |
| redis    | Job queue and status store    | 6379 internal |

## Architecture

Browser -> Frontend (3000) -> API (8000) -> Redis
                                              ^
                                           Worker

## Environment Variables

| Variable         | Description                   | Default           |
|------------------|-------------------------------|-------------------|
| REDIS_PASSWORD   | Redis authentication password | -                 |
| REDIS_HOST       | Redis hostname                | redis             |
| REDIS_PORT       | Redis port                    | 6379              |
| QUEUE_KEY        | Redis queue key name          | jobs              |
| API_URL          | API URL used by the frontend  | http://api:8000   |

## Running Tests

cd api
pip install -r requirements.txt
pytest tests/ -v

## CI/CD Pipeline

The GitHub Actions pipeline runs on every push to main:

lint -> test -> build -> security scan -> integration test -> deploy

- lint: flake8 (Python), eslint (JavaScript), hadolint (Dockerfiles)
- test: pytest with coverage report uploaded as artifact
- build: builds and pushes all images to a local registry tagged with git SHA
- security: Trivy scans all images, fails on CRITICAL findings, uploads SARIF results
- integration: brings full stack up, submits a job, asserts completion, tears down
- deploy: rolling update on pushes to main only, health-checked before cutover

## Successful Startup

You should see:

redis-1    | Ready to accept connections tcp
api-1      | Uvicorn running on http://0.0.0.0:8000
worker-1   | Processing job ...
frontend-1 | Frontend running on port 3000# hng14-stage2-devops
