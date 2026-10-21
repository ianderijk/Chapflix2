from unittest.mock import patch

from app.src.callbacks import browse

USER = {"name": "Chap", "id": 2}


def _select_show(show: str, seasons: list[int], last_played: dict) -> dict:
    with (
        patch.object(
            browse, "clicked", return_value={"type": "show-card", "index": show}
        ),
        patch.object(browse.api, "get_season_options", return_value=seasons),
        patch.object(browse.api, "get_last_played_selection", return_value=last_played),
    ):
        return browse.select_show([1], [], None, USER)


def test_select_show_defaults_to_first_season_for_other_shows():
    selection = _select_show("TheOffice", [1, 2], {"show": "SouthPark", "season": 5})
    assert selection == {"show": "TheOffice", "season": 1}


def test_select_show_opens_last_played_season():
    selection = _select_show("SouthPark", [1, 5, 6], {"show": "SouthPark", "season": 5})
    assert selection == {"show": "SouthPark", "season": 5}


def test_select_show_without_seasons_stores_no_season():
    selection = _select_show("Empty", [], {"show": "SouthPark", "season": 5})
    assert selection == {"show": "Empty", "season": None}


def test_season_tab_keeps_the_show_and_changes_season():
    with patch.object(
        browse, "clicked", return_value={"type": "season-tab", "index": 3}
    ):
        selection = browse.select_show(
            [], [1], {"show": "SouthPark", "season": 5}, USER
        )
    assert selection == {"show": "SouthPark", "season": 3}
