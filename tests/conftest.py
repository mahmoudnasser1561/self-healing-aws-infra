import pytest

from app import create_app
from app.config import load_settings
from app.db import Database


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def database(settings):
    with Database(settings).connection() as conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS todos")
    return Database(settings)


@pytest.fixture
def cur(database):
    with database.connection() as conn, conn.cursor() as cursor:
        yield cursor


@pytest.fixture
def client(settings, database):
    return create_app(settings, database).test_client()
