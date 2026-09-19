import pytest

from app import create_app
from app.db import Database


@pytest.fixture
def database():
    with Database().connection() as conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS components")
    return Database()


@pytest.fixture
def client(database):
    return create_app(database).test_client()
