import dataclasses

import pytest

from app import create_app
from app.config import load_config


@pytest.fixture
def config():
    return dataclasses.replace(load_config({}), db_port=1)


@pytest.fixture
def client(config):
    return create_app(config).test_client()
