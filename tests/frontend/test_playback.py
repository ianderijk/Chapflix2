from unittest.mock import patch

import dash
import pytest

from app.src import player
from app.src.callbacks import playback
from app.src.layout import ID_ENDED_STORE, ID_HERO_NEXT, ID_UP_NEXT_PLAY

USER = {"name": "Chap", "id": 2}
PLAY_ID = 1700000000000


def _episode(show: str, season: int, episode: int, file_key: int = 99) -> dict:
    return {
        "file": str(player.MEDIA_FILES / "content" / show / f"S{season}E{episode}.mp4"),
        "file_key": file_key,
        "show": show,
        "season": season,
        "episode": episode,
        "plays": None,
        "last_played": None,
        "duration": 1325,
    }


def _dispatch(trigger, show_selection=None, up_next=None, dismissed=None, request=None):
    inputs = (None,) * 7
    states = (USER, show_selection, up_next, dismissed, request)
    with patch.object(playback, "clicked", return_value=trigger):
        return playback.dispatch_play(*inputs, *states)


def test_play_request_carries_what_the_countdown_needs():
    with patch.object(player.time, "time", return_value=PLAY_ID / 1000):
        request = player.build_play_request(_episode("TheOffice", 1, 4), start_at=71.5)
    assert request["play_id"] == PLAY_ID
    assert request["src"] == f"content/TheOffice/S1E4.mp4?play={PLAY_ID}#t=71.5"
    assert request["media_type"] == "show"
    assert request["duration"] == 1325
    assert request["file_key"] == 99


def test_films_are_identified_as_films():
    film = {**_episode("Aliens", 1, 1), "film": "Aliens"}
    assert player.build_play_request(film)["media_type"] == "film"


def test_episode_in_show_not_last_played_plays_without_choosing_a_season():
    """Regression: an unset season sent /show/<show>/None/<episode> to the API."""
    episode = _episode("TheOffice", 1, 4)
    tile = {"type": "episode-tile", "index": 4}
    with (
        patch.object(
            playback.api, "get_episode_selection_data", return_value=episode
        ) as get_episode,
        patch.object(playback.api, "record_watched") as record_watched,
    ):
        request, notice = _dispatch(tile, {"show": "TheOffice", "season": 1})
    get_episode.assert_called_once_with("TheOffice", 1, 4)
    record_watched.assert_called_once_with(episode, USER["id"])
    assert request["src"].startswith("content/TheOffice/S1E4.mp4")
    assert notice == ""


def test_episode_click_without_a_season_does_not_call_the_api():
    tile = {"type": "episode-tile", "index": 4}
    with patch.object(playback.api, "get_episode_selection_data") as get_episode:
        assert _dispatch(tile, {"show": "X", "season": None}) == (
            dash.no_update,
            dash.no_update,
        )
    get_episode.assert_not_called()


def test_hero_next_records_the_play_so_up_next_follows_it():
    episode = _episode("TheSimpsons", 4, 5)
    with (
        patch.object(playback.api, "get_next_episode_selection", return_value=episode),
        patch.object(playback.api, "record_watched") as record_watched,
    ):
        request, _ = _dispatch(ID_HERO_NEXT)
    record_watched.assert_called_once_with(episode, USER["id"])
    assert request["src"].startswith("content/TheSimpsons/S4E5.mp4")


@pytest.mark.parametrize("trigger", [ID_ENDED_STORE, ID_UP_NEXT_PLAY])
def test_queued_episode_plays_on_end_or_play_now(trigger):
    episode = _episode("TheSimpsons", 4, 4)
    up_next = {"play_id": PLAY_ID, "selection": episode, "title": ""}
    with patch.object(playback.api, "record_watched") as record_watched:
        request, _ = _dispatch(trigger, up_next=up_next, request={"play_id": PLAY_ID})
    record_watched.assert_called_once_with(episode, USER["id"])
    assert request["src"].startswith("content/TheSimpsons/S4E4.mp4")


@pytest.mark.parametrize(
    ("up_next", "dismissed"),
    [
        pytest.param(
            {"play_id": PLAY_ID, "selection": _episode("A", 1, 2), "title": ""},
            {"play_id": PLAY_ID},
            id="dismissed",
        ),
        pytest.param(
            {"play_id": PLAY_ID - 1, "selection": _episode("A", 1, 2), "title": ""},
            None,
            id="queued-for-an-earlier-playback",
        ),
        pytest.param(
            {"play_id": PLAY_ID, "selection": None, "title": ""},
            None,
            id="no-next-episode",
        ),
        pytest.param(None, None, id="nothing-queued"),
    ],
)
def test_nothing_plays_on_end_when_no_episode_is_queued(up_next, dismissed):
    with patch.object(playback.api, "record_watched") as record_watched:
        result = _dispatch(
            ID_ENDED_STORE,
            up_next=up_next,
            dismissed=dismissed,
            request={"play_id": PLAY_ID},
        )
    assert result == (dash.no_update, dash.no_update)
    record_watched.assert_not_called()


def test_up_next_is_fetched_once_per_playback():
    countdown = {"play_id": PLAY_ID, "seconds": 9}
    episode = _episode("TheSimpsons", 4, 4)
    with patch.object(
        playback.api, "get_next_episode_selection", return_value=episode
    ) as get_next:
        up_next = playback.prepare_up_next(countdown, None, USER)
        again = playback.prepare_up_next({**countdown, "seconds": 8}, up_next, USER)
    get_next.assert_called_once_with("Chap")
    assert up_next == {
        "play_id": PLAY_ID,
        "selection": episode,
        "title": "The Simpsons · S4 E4",
    }
    assert again is dash.no_update


def test_up_next_without_a_next_episode_is_remembered_as_empty():
    with patch.object(
        playback.api, "get_next_episode_selection", side_effect=playback.ApiError
    ):
        up_next = playback.prepare_up_next(
            {"play_id": PLAY_ID, "seconds": 9}, None, USER
        )
    assert up_next == {"play_id": PLAY_ID, "selection": None, "title": ""}


def test_pause_is_recorded_against_the_file():
    with patch.object(playback.api, "record_paused") as record_paused:
        playback.record_pause({"file_key": 74, "seconds": 42.0}, USER)
    record_paused.assert_called_once_with(USER["id"], 74, 42.0)
