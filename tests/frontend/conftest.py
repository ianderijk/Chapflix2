from pathlib import Path

import pytest

from app.src import config

MEDIA_FILES = Path("/media/test/Chapflix2")


@pytest.fixture(autouse=True)
def frontend_config(monkeypatch):
    """Point every test at an address that can't resolve, so an unmocked API call
    fails instead of reaching a real API."""
    monkeypatch.setenv(config.API_URL_VARIABLE, "http://api.invalid/")
    monkeypatch.setenv(config.MEDIA_FILES_VARIABLE, str(MEDIA_FILES))
