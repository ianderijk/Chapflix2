from typing import Literal
from pathlib import Path
from datetime import datetime

MEDIA_FILES = Path("/media/ianderijk/Backup/Chapflix2/")


def drop_down_lists(lst: list[str]) -> list[dict[str, str]]:
    return [{"label": x, "value": x} for x in lst]


def _format_filepath(filepath: str) -> Path:
    return Path(filepath).relative_to(MEDIA_FILES)


def _format_play_timestamp(timestamp: str | None) -> str:
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
        return f"{dt.hour:02}:{dt.minute:02} {dt.day:02}-{dt.month:02}-{dt.year}"
    return "Never!"


def _format_episode_string(selection: dict) -> str:
    return f"{selection['show']}: Season {selection['season']}, Episode {selection['episode']}"


def get_display_string(selection: dict, content_type: Literal["show", "film"]) -> str:
    play_timestamp = _format_play_timestamp(selection["last_played"])
    play_information = (
        f"Last played: {play_timestamp} | Played {selection['plays']} times"
    )
    match content_type:
        case "show":
            display_string = (
                _format_episode_string(selection) + " | " + play_information
            )
        case "film":
            display_string = selection["film"] + play_information
    return display_string


def get_file(payload: dict) -> Path:
    file = payload["file"]
    return _format_filepath(file)
