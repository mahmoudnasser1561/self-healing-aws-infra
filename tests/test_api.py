import time
from datetime import datetime

from app import create_app, routes
from app.db import Database
from app.seed import COMPONENTS


def test_components_returns_every_seeded_row(client):
    response = client.get("/api/components")

    assert response.status_code == 200
    rows = response.get_json()["components"]
    assert [row["name"] for row in rows] == [name for name, _, _ in COMPONENTS]
    assert set(rows[0]) == {"id", "name", "tier", "description"}


def test_components_cover_the_seeded_tiers(client):
    rows = client.get("/api/components").get_json()["components"]

    assert {row["tier"] for row in rows} == {tier for _, tier, _ in COMPONENTS}


def test_health_reports_database_state(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["components"] == len(COMPONENTS)
    datetime.fromisoformat(body["db_time"])


def test_health_db_time_advances_between_calls(client):
    first = client.get("/api/health").get_json()["db_time"]
    time.sleep(0.05)
    second = client.get("/api/health").get_json()["db_time"]

    assert datetime.fromisoformat(second) > datetime.fromisoformat(first)


def test_health_reports_the_release_version(client, tmp_path, monkeypatch):
    version_file = tmp_path / "VERSION"
    version_file.write_text("abc123\n")
    monkeypatch.setattr(routes, "VERSION_FILE", version_file)

    assert client.get("/api/health").get_json()["version"] == "abc123"


def test_health_version_defaults_to_dev(client, tmp_path, monkeypatch):
    monkeypatch.setattr(routes, "VERSION_FILE", tmp_path / "missing")

    assert client.get("/api/health").get_json()["version"] == "dev"


def test_health_is_unavailable_when_the_database_is_down(monkeypatch):
    monkeypatch.setenv("DB_PORT", "1")

    response = create_app(Database()).test_client().get("/api/health")

    assert response.status_code == 503
    assert response.get_json()["status"] == "unavailable"


def test_seeding_twice_does_not_duplicate_rows(database):
    for _ in range(2):
        with Database().connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) AS total FROM components")
            total = cur.fetchone()["total"]

    assert total == len(COMPONENTS)
