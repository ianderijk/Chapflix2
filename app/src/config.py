import os
from pathlib import Path

API_URL_VARIABLE = "CHAPFLIX_API_URL"
MEDIA_FILES_VARIABLE = "CHAPFLIX_MEDIA_FILES"


class MissingConfigurationError(Exception):
    """Raised when a required environment variable isn't set."""


def _required(variable: str) -> str:
    value = os.environ.get(variable)
    if not value:
        raise MissingConfigurationError(
            f"{variable} must be set; see app/README.md for what it should contain"
        )
    return value


def api_url() -> str:
    return _required(API_URL_VARIABLE)


def media_files() -> Path:
    """The prefix stripped from the API's file paths to get a path under content/."""
    return Path(_required(MEDIA_FILES_VARIABLE))


def check() -> None:
    """Fail at startup rather than on the first request."""
    api_url()
    media_files()
