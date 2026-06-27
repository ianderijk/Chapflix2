import pytest  # noqa: F401
from pathlib import Path
from unittest.mock import patch
import app.src.player as player
from app.src.player import (
    AutoPlayed,
    LastPlayed,
    User,
    Player,
    get_last_played,
    get_user,
    get_file_key,
    drop_down_lists,
    get_auto_play,
    get_play_num,
)


def test_get_last_played(setup_test_db):
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


def test_get_user(setup_test_db):
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


def test_get_auto_play_next(setup_test_db):
    test_user = User(1, "Test")
    result = get_auto_play("next", test_user)
    expected = AutoPlayed(
        file="/media/ianderijk/Backup/Chapflix2/content/TestShow/S1E2.mp4",
        show="TestShow",
        season=1,
        episode=2,
    )
    assert result == expected


def test_get_auto_play_previous(setup_test_db):
    test_user = User(1, "Test")
    result = get_auto_play("previous", test_user)
    expected = AutoPlayed(file=None, show=None, season=None, episode=None)
    assert result == expected


def test_get_play_num(setup_test_db):
    user = User(1, "TestUser")
    result = get_play_num(user)
    expected = 1
    assert result == expected


class TestPlayer:
    player = Player()

    def test_set_user(self):
        user_name = "Test"
        TestPlayer.player.user = user_name
        assert TestPlayer.player.user.id_ == 1
        assert TestPlayer.player.user.name == "Test"
