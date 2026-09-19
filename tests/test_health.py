import dataclasses
import time
from datetime import datetime

from app import create_app
from app.config import load_settings, load_version
from app.db import Database


def test_health_reports_database_state(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["todos"] == 0
    datetime.fromisoformat(body["db_time"])


def test_health_db_time_advances_between_calls(client):
    first = client.get("/api/health").get_json()["db_time"]
    time.sleep(0.05)
    second = client.get("/api/health").get_json()["db_time"]

    assert datetime.fromisoformat(second) > datetime.fromisoformat(first)


def test_health_reports_the_release_version(settings, database):
    versioned = dataclasses.replace(settings, version="abc123")

    body = create_app(versioned, database).test_client().get("/api/health").get_json()

    assert body["version"] == "abc123"


def test_health_is_unavailable_when_the_database_is_down(settings):
    broken = dataclasses.replace(settings, db_port=1)

    response = create_app(broken, Database(broken)).test_client().get("/api/health")

    assert response.status_code == 503
    assert response.get_json()["status"] == "unavailable"


def test_version_is_read_from_the_release_file(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("abc123\n")

    assert load_version(version_file) == "abc123"
    assert load_version(tmp_path / "missing") == "dev"


def test_settings_default_the_page_limits():
    settings = load_settings({})

    assert (settings.default_limit, settings.max_limit) == (20, 100)
