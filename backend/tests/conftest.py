import os
import sys
from pathlib import Path
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_client(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'videos.db'}"
    os.environ["DATA_DIR"] = str(tmp_path / "data")
    os.environ["AI_TAGGING_ENABLED"] = "0"

    (tmp_path / "data").mkdir(parents=True, exist_ok=True)

    backend_path = Path(__file__).resolve().parents[1]
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    import database
    import main

    importlib.reload(database)
    importlib.reload(main)

    client = TestClient(main.app)
    return client, database, main
