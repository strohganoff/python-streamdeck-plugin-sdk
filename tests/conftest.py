import random
import uuid

import pytest


@pytest.fixture
def port_number():
    """Fixture to provide a random 4-digit port number for each test."""
    return random.randint(1000, 9999)


@pytest.fixture
def plugin_registration_uuid() -> str:
    return str(uuid.uuid1())
