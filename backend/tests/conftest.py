import os
import sys
from pathlib import Path

# Для тестів API використовується окрема SQLite-БД, симуляція вимкнена
TEST_DB = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SIMULATION_ENABLED"] = "0"
os.environ["SEED_DEMO_DATA"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    if TEST_DB.exists():
        TEST_DB.unlink()
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
    from app.db.session import engine

    engine.dispose()
    TEST_DB.unlink(missing_ok=True)


def login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
