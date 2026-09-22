from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from services.api.main import create_app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app = create_app("sqlite+pysqlite:///:memory:")
    with TestClient(app) as test_client:
        yield test_client

