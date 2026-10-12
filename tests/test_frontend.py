from unittest.mock import patch

from app import main
from app.src.player import MEDIA_FILES

USER = {"name": "Chap", "id": 2}


def _select_show(show: str, seasons: list[int], last_played: dict) -> dict:
    with (
        patch.object(
            main, "_clicked", return_value={"type": "show-card", "index": show}
        ),
        patch.object(main.api, "get_season_options", return_value=seasons),
        patch.object(main.api, "get_last_played_selection", return_value=last_played),
    ):
        return main.select_show([1], [], None, USER)


def test_select_show_defaults_to_first_season_for_other_shows():
    selection = _select_show("TheOffice", [1, 2], {"show": "SouthPark", "season": 5})
    assert selection == {"show": "TheOffice", "season": 1}


def test_select_show_opens_last_played_season():
    selection = _select_show("SouthPark", [1, 5, 6], {"show": "SouthPark", "season": 5})
    assert selection == {"show": "SouthPark", "season": 5}


def test_episode_in_show_not_last_played_plays_without_choosing_a_season():
    """Regression: the season was left as None, so episode clicks requested
    /show/<show>/None/<episode> and nothing played."""
    selection = _select_show("TheOffice", [1, 2], {"show": "SouthPark", "season": 5})
    episode = {
        "file": str(MEDIA_FILES / "content" / "TheOffice" / "S1E4.mp4"),
        "file_key": 99,
        "show": "TheOffice",
        "season": 1,
        "episode": 4,
        "plays": None,
        "last_played": None,
    }
    tile = {"type": "episode-tile", "index": 4}
    with (
        patch.object(main, "_clicked", return_value=tile),
        patch.object(
            main.api, "get_episode_selection_data", return_value=episode
        ) as get_episode,
        patch.object(main.api, "record_watched") as record_watched,
    ):
        request, notice = main.dispatch_play(
            None, None, None, [], [1], None, None, USER, selection, None
        )

    get_episode.assert_called_once_with("TheOffice", 1, 4)
    record_watched.assert_called_once_with(episode, USER["id"])
    assert request["file"] == "content/TheOffice/S1E4.mp4"
    assert notice == ""


def test_episode_click_without_a_season_does_not_call_the_api():
    tile = {"type": "episode-tile", "index": 4}
    with (
        patch.object(main, "_clicked", return_value=tile),
        patch.object(main.api, "get_episode_selection_data") as get_episode,
    ):
        main.dispatch_play(
            None,
            None,
            None,
            [],
            [1],
            None,
            None,
            USER,
            {"show": "X", "season": None},
            None,
        )
    get_episode.assert_not_called()
