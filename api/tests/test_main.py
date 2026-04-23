import pytest
from unittest.mock import MagicMock, patch

with patch("redis.Redis") as mock_redis_cls:
    mock_instance = MagicMock()
    mock_redis_cls.return_value = mock_instance
    from main import app

from fastapi.testclient import TestClient
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock():
    mock_instance.reset_mock()


def test_health_ok():
    mock_instance.ping.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_fails_when_redis_down():
    import redis as redis_lib
    mock_instance.ping.side_effect = redis_lib.exceptions.ConnectionError
    response = client.get("/health")
    assert response.status_code == 503


def test_create_job_returns_job_id():
    mock_instance.lpush.return_value = 1
    mock_instance.hset.return_value = 1
    response = client.post("/jobs")
    assert response.status_code == 200
    assert "job_id" in response.json()


def test_create_job_pushes_to_queue():
    mock_instance.lpush.return_value = 1
    mock_instance.hset.return_value = 1
    response = client.post("/jobs")
    job_id = response.json()["job_id"]
    mock_instance.lpush.assert_called_once_with("jobs", job_id)


def test_get_job_returns_status():
    mock_instance.hget.return_value = b"queued"
    response = client.get("/jobs/test-id")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_get_job_returns_404_when_missing():
    mock_instance.hget.return_value = None
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404


def test_get_job_returns_completed_status():
    mock_instance.hget.return_value = b"completed"
    response = client.get("/jobs/done-id")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
