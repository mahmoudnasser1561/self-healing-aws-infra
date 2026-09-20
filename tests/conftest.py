import pytest

from app import create_app
from app.config import load_settings


@pytest.fixture
def settings():
    return load_settings({})


@pytest.fixture
def client(settings):
    return create_app(settings).test_client()
