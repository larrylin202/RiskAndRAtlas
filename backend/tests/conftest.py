import pytest
import requests

from app import create_app
from app.api import geocode
from app.services import search_cache

class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload

class FakeNominatim:
    """Replaces requests.get. Tests set payload/status/error and inspect calls."""

    def __init__(self):
        self.payload = []
        self.status = 200
        self.error = None
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self.error is not None:
            raise self.error
        return FakeResponse(self.payload, self.status)

class FakeClock:
    """Replaces the 'time' module inside geocode.py and search_cache.py"""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []
        self.sleep_advances_time = True

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        if self.sleep_advances_time:
            self.now += seconds


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True, 
        MIN_SECONDS_BETWEEN_CALLS=1,
        MAX_WAIT_SECONDS=3,
        CACHE_SECONDS=30,
        MAX_CACHE_SIZE=10
        )
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    monkeypatch.setattr(search_cache, "_search_cache", {})
    monkeypatch.setattr(search_cache, "_next_call_at", 0.0)


@pytest.fixture(autouse=True)
def nominatim(monkeypatch):
    fake = FakeNominatim()
    monkeypatch.setattr(geocode.requests, "get", fake.get)
    return fake

@pytest.fixture(autouse=True)
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(geocode, "time", fake)
    monkeypatch.setattr(search_cache, "time", fake)
    return fake