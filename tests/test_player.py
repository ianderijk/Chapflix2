import pytest  # noqa: F401
from pathlib import Path
from unittest.mock import patch
import app.src.player as player
from app.src.player import (
    LastPlayed,
    User,
    get_last_played,
    get_user,
    get_file_key,
    drop_down_lists,
)


def test_get_last_played():
    with patch(
        "app.src.player.execute_query",
        return_value=[
            (
                "show",
                1,
                None,
                "Show",
                1,
                1,
                "/media/ianderijk/Backup/Chapflix2/Content/Show/S1E1.mp4",
            )
        ],
    ):
        result = get_last_played(1)
    expected = LastPlayed(
        "show",
        1,
        None,
        "Show",
        1,
        1,
        "/media/ianderijk/Backup/Chapflix2/Content/Show/S1E1.mp4",
    )
    assert result == expected


def test_get_user():
    with patch("app.src.player.execute_query", return_value=[(1,)]):
        result = get_user("Test")
    expected = User(1, "Test")
    assert result == expected


def test_get_file_key():
    with patch.object(player, "FILE_KEYS", {Path("path/to/file"): 1}):
        result = get_file_key(Path("path/to/file"))
    expected = 1
    assert result == expected


def test_drop_down_lists():
    lst = ["test1", "test2"]
    result = drop_down_lists(lst)
    expected = [
        {"label": "test1", "value": "test1"},
        {"label": "test2", "value": "test2"},
    ]
    assert result == expected
