import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.main import main
from src.services.pypi import Pypi as PypiService
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_service(mock_repo):
    return PypiService(mock_repo)


@pytest.fixture
def client():
    app = main()
    return TestClient(app)
