import hashlib
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.src import config

CARD_PALETTES = [
    ("#5c0a14", "#1a0306"),
    ("#3b1450", "#0e0514"),
    ("#123a3a", "#040f10"),
    ("#4a3410", "#120c03"),
    ("#2a2f4a", "#08090f"),
    ("#3d4a14", "#0d1003"),
]


def _format_filepath(filepath: str) -> Path:
    return Path(filepath).relative_to(config.media_files())


def format_play_timestamp(timestamp: str | None) -> str:
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
        return f"{dt.hour:02}:{dt.minute:02} {dt.day:02}-{dt.month:02}-{dt.year}"
    return "Never!"


def format_seconds(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02}:{secs:02}"
    return f"{minutes}:{secs:02}"


def pretty_title(name: str) -> str:
    """Turn database names like 'TheThickOfIt' into 'The Thick Of It'."""
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", " ", name)
    return re.sub(r":(?=\S)", ": ", spaced)


def card_palette(name: str) -> tuple[str, str]:
    """A stable stained-glass gradient for a title, so each card keeps its colour."""
    digest = hashlib.md5(name.encode()).digest()
    return CARD_PALETTES[digest[0] % len(CARD_PALETTES)]


def get_media_type(selection: dict[str, Any]) -> str:
    return "film" if selection.get("film") else "show"


def get_title(selection: dict[str, Any]) -> str:
    return pretty_title(selection.get("film") or selection.get("show") or "")


def get_subtitle(selection: dict[str, Any]) -> str:
    if get_media_type(selection) == "film":
        return "Feature film"
    return f"Season {selection['season']} · Episode {selection['episode']}"


def get_episode_label(selection: dict[str, Any]) -> str:
    return f"S{selection['season']} E{selection['episode']}"


def get_play_information(selection: dict[str, Any]) -> str:
    play_information = (
        f"Last played: {format_play_timestamp(selection.get('last_played'))}"
        f" | Runtime {format_seconds(selection['duration'])}"
    )
    if selection.get("plays") is not None:
        play_information += f" | Played {selection['plays']} times"
    return play_information


def get_file(payload: dict) -> Path:
    file = payload["file"]
    return _format_filepath(file)


def build_play_request(selection: dict[str, Any], start_at: float = 0) -> dict:
    """Everything the player and the up-next countdown need about one playback.

    `play_id` is unique per request: it forces the browser to reload the video
    even when the same file is played again, and lets the countdown tell which
    playback its state belongs to.
    """
    play_id = int(time.time() * 1000)
    src = f"{get_file(selection)}?play={play_id}"
    if start_at:
        src += f"#t={start_at}"
    return {
        "play_id": play_id,
        "src": src,
        "file_key": selection["file_key"],
        "media_type": get_media_type(selection),
        "duration": selection["duration"],
        "title": get_title(selection),
        "subtitle": get_subtitle(selection),
        "meta": get_play_information(selection),
    }
