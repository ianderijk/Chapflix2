import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

MEDIA_FILES = Path(
    os.environ.get("CHAPFLIX_MEDIA_FILES", "/media/ianderijk/Backup/Chapflix2/")
)

# Gradient pairs used to give each title card its own stained-glass colouring
CARD_PALETTES = [
    ("#5c0a14", "#1a0306"),  # oxblood
    ("#3b1450", "#0e0514"),  # bruised violet
    ("#123a3a", "#040f10"),  # verdigris
    ("#4a3410", "#120c03"),  # tarnished brass
    ("#2a2f4a", "#08090f"),  # midnight
    ("#3d4a14", "#0d1003"),  # absinthe
]


def _format_filepath(filepath: str) -> Path:
    return Path(filepath).relative_to(MEDIA_FILES)


def format_play_timestamp(timestamp: str | None) -> str:
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
        return f"{dt.hour:02}:{dt.minute:02} {dt.day:02}-{dt.month:02}-{dt.year}"
    return "Never!"


def pretty_title(name: str) -> str:
    """Turn database names like 'TheThickOfIt' into 'The Thick Of It'."""
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", " ", name)
    return re.sub(r":(?=\S)", ": ", spaced)


def card_palette(name: str) -> tuple[str, str]:
    digest = hashlib.md5(name.encode()).digest()
    return CARD_PALETTES[digest[0] % len(CARD_PALETTES)]


def get_title(selection: dict[str, Any]) -> str:
    return pretty_title(selection.get("film") or selection.get("show") or "")


def get_subtitle(selection: dict[str, Any]) -> str:
    if selection.get("film"):
        return "Feature film"
    return f"Season {selection['season']} · Episode {selection['episode']}"


def get_play_information(selection: dict[str, Any]) -> str:
    play_information = (
        f"Last played: {format_play_timestamp(selection.get('last_played'))}"
    )
    if selection.get("plays") is not None:
        play_information += f" | Played {selection['plays']} times"
    return play_information


def is_playable(selection: dict[str, Any] | None) -> bool:
    """Next/previous episode lookups return null fields when there's nothing to play."""
    return bool(selection and selection.get("file"))


def get_file(payload: dict) -> Path:
    file = payload["file"]
    return _format_filepath(file)
