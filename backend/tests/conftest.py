import pytest
import database
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient backed by a throwaway SQLite database."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as c:
        yield c
