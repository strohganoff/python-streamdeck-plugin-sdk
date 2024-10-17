import random

import pytest


@pytest.fixture
def port_number():
    """Fixture to provide a random 4-digit port number for each test."""
    return random.randint(1000, 9999)
