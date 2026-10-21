from unittest.mock import patch

import dash

from app.src.callbacks import billboard

USER = {"name": "Chap", "id": 2}
LAST_PLAYED = {
    "media_type": "show",
    "file": "/media/content/TheSimpsons/S4E3.mp4",
    "file_key": 1,
    "show": "TheSimpsons",
    "season": 4,
    "episode": 3,
    "plays": None,
    "last_played": "2026-10-20T12:06:35",
    "duration": 1325,
}
NEXT = {**LAST_PLAYED, "episode": 4, "file_key": 74}


def _render(previous=None, next_=NEXT, neighbour_error=None):
    with (
        patch.object(
            billboard.api, "get_last_played_selection", return_value=LAST_PLAYED
        ),
        patch.object(
            billboard.api, "get_continue_watching_from", return_value=71.0
        ) as paused_at,
        patch.object(
            billboard.api,
            "get_previous_episode_selection",
            return_value=previous,
            side_effect=neighbour_error,
        ),
        patch.object(billboard.api, "get_next_episode_selection", return_value=next_),
    ):
        result = billboard.render_billboard(None, None, USER)
    return result, paused_at


def test_paused_position_is_looked_up_for_the_last_played_file():
    result, paused_at = _render()
    paused_at.assert_called_once_with(USER["id"], 1)
    assert result[3].endswith("Paused at 1:11")


def test_missing_neighbour_hides_its_button_without_a_notice():
    result, _ = _render(previous=None, next_=NEXT)
    previous_label, previous_class, next_label, next_class, notice = result[5:]
    assert (previous_label, previous_class) == ("", billboard.HIDDEN)
    assert (next_label, next_class) == ("⏭ S4 E4", billboard.GHOST)
    assert notice is dash.no_update


def test_api_failure_finding_neighbours_is_reported():
    result, _ = _render(neighbour_error=billboard.ApiError)
    assert result[5:9] == ("", billboard.HIDDEN, "", billboard.HIDDEN)
    assert result[9] == "Couldn't find the neighbouring episodes."
