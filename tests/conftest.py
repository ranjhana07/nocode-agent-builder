from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mockplatform.main import create_platform_app


@pytest.fixture()
def platform() -> TestClient:
    return TestClient(create_platform_app("sqlite://"))
