import os
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from server.database import init_db
from server.server import app

@pytest.fixture(scope="session", autouse=True)
def test_env():
    # Use temporary database for test session
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    os.environ["SYSWATCH_DB_PATH"] = test_db_path
    init_db(Path(test_db_path))

    yield test_db_path

    # Clean up test database
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
