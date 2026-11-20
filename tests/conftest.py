import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def offline_weather(monkeypatch):
    """Tests never touch the network; weather falls back to seasonal estimates."""

    def refuse(*args, **kwargs):
        raise requests.ConnectionError("network disabled in tests")

    monkeypatch.setattr(requests, "get", refuse)
    from travel_agent.tools import weather

    weather._CACHE.clear()
