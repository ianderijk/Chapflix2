from typing import Any, Literal

import requests

from app.src import config

TIMEOUT_SECONDS = 5


class ApiError(Exception):
    """Raised when the Chapflix API can't be reached or returns an error."""


def _url(endpoint: str) -> str:
    return config.api_url().rstrip("/") + "/" + endpoint


def _get(endpoint: str) -> Any:
    try:
        response = requests.get(_url(endpoint), timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise ApiError(f"GET {endpoint} failed: {error}") from error


def _post(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(_url(endpoint), json=data, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise ApiError(f"POST {endpoint} failed: {error}") from error


def get_user_id(user: str) -> int:
    return _get(f"user/{user}")["id_"]


def get_playable_content(content_type: Literal["shows", "films"]) -> list[str]:
    return _get(content_type)[content_type]


def get_season_options(show: str) -> list[int]:
    return _get(f"show/{show}/seasons")["seasons"]


def get_episode_options(show: str, season: int) -> list[int]:
    return _get(f"show/{show}/{season}")["episodes"]


def get_episode_selection_data(show: str, season: int, episode: int) -> dict[str, Any]:
    return _get(f"show/{show}/{season}/{episode}")


def get_film(film: str) -> dict[str, Any]:
    return _get(f"film/{film}")


def get_next_episode_selection(user: str) -> dict[str, Any] | None:
    """The episode after the user's last play, or None at the end of a show."""
    return _get(f"user/{user}/next-episode")


def get_previous_episode_selection(user: str) -> dict[str, Any] | None:
    """The episode before the user's last play, or None at the start of a show."""
    return _get(f"user/{user}/previous-episode")


def get_last_played_selection(user: str) -> dict[str, Any]:
    return _get(f"user/{user}/last-played")


def get_continue_watching_from(user_id: int, file_key: int) -> float:
    """Where the user last paused this file, or 0.0 if they never have."""
    return _get(f"get-paused/{user_id}/{file_key}")["seconds"]


def record_watched(selection: dict[str, Any], user_id: int) -> None:
    _post(
        "record-play",
        {
            "film": selection.get("film"),
            "show": selection.get("show"),
            "season": selection.get("season"),
            "episode": selection.get("episode"),
            "user_id": user_id,
            "file_key": selection["file_key"],
        },
    )


def record_paused(user_id: int, file_key: int, seconds: float) -> None:
    _post(
        "record-paused",
        {"user_id": user_id, "file_key": file_key, "video_progress": seconds},
    )
