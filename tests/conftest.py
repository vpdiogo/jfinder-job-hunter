import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    database_path = tmp_path / "jfinder-test.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    with TestClient(app) as test_client:
        yield test_client
