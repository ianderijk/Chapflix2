from typing import Any

import dash
from dash import (
    ALL,
    ClientsideFunction,
    Input,
    Output,
    State,
    callback,
    clientside_callback,
)

from app.src import api_client as api
from app.src.api_client import ApiError
from app.src.callbacks.triggers import clicked
from app.src.layout import (
    ID_COUNTDOWN_STORE,
    ID_DISMISSED_STORE,
    ID_ENDED_STORE,
    ID_HERO_NEXT,
    ID_HERO_PREV,
    ID_HERO_RESUME,
    ID_NOTICE,
    ID_NOW_PLAYING_META,
    ID_NOW_PLAYING_SUBTITLE,
    ID_NOW_PLAYING_TITLE,
    ID_PAUSED_STORE,
    ID_PLAY_REQUEST_STORE,
    ID_PLAYER,
    ID_SHOW_SELECTION_STORE,
    ID_THEATRE,
    ID_UP_NEXT,
    ID_UP_NEXT_CANCEL,
    ID_UP_NEXT_COUNT,
    ID_UP_NEXT_PLAY,
    ID_UP_NEXT_STORE,
    ID_UP_NEXT_TITLE,
    ID_USER_STORE,
    ID_VIDEO_EVENTS,
    TYPE_EPISODE_TILE,
    TYPE_FILM_CARD,
)
from app.src.player import build_play_request, get_episode_label, get_title

clientside_callback(
    ClientsideFunction(namespace="chapflix", function_name="trackPlayback"),
    Output(ID_PAUSED_STORE, "data"),
    Output(ID_COUNTDOWN_STORE, "data"),
    Output(ID_ENDED_STORE, "data"),
    Input(ID_VIDEO_EVENTS, "event"),
    State(ID_PLAY_REQUEST_STORE, "data"),
    State(ID_COUNTDOWN_STORE, "data"),
    prevent_initial_call=True,
)

clientside_callback(
    ClientsideFunction(namespace="chapflix", function_name="renderUpNext"),
    Output(ID_UP_NEXT, "className"),
    Output(ID_UP_NEXT_TITLE, "children"),
    Output(ID_UP_NEXT_COUNT, "children"),
    Input(ID_COUNTDOWN_STORE, "data"),
    Input(ID_UP_NEXT_STORE, "data"),
    Input(ID_DISMISSED_STORE, "data"),
    prevent_initial_call=True,
)

clientside_callback(
    ClientsideFunction(namespace="chapflix", function_name="dismissUpNext"),
    Output(ID_DISMISSED_STORE, "data"),
    Input(ID_UP_NEXT_CANCEL, "n_clicks"),
    State(ID_COUNTDOWN_STORE, "data"),
    prevent_initial_call=True,
)


def _queued_episode(
    up_next: dict | None, dismissed: dict | None, play_request: dict | None
) -> dict[str, Any] | None:
    """The next episode lined up for the current playback, unless it was dismissed."""
    if not up_next or not play_request or not up_next["selection"]:
        return None
    play_id = play_request["play_id"]
    if up_next["play_id"] != play_id:
        return None
    if dismissed and dismissed["play_id"] == play_id:
        return None
    return up_next["selection"]


def _resume(user: dict) -> dict[str, Any]:
    last_played = api.get_last_played_selection(user["name"])
    seconds = api.get_continue_watching_from(user["id"])
    return build_play_request(last_played, seconds)


def _record_and_play(selection: dict[str, Any], user: dict) -> dict[str, Any]:
    api.record_watched(selection, user["id"])
    return build_play_request(selection)


def _selection_for(trigger: Any, user: dict, show_selection: dict | None):
    """The selection a browse or hero click asks for, or None if it can't be played."""
    name = user["name"]
    if trigger == ID_HERO_PREV:
        return api.get_previous_episode_selection(name)
    if trigger == ID_HERO_NEXT:
        return api.get_next_episode_selection(name)
    if not isinstance(trigger, dict):
        return None
    if trigger["type"] == TYPE_FILM_CARD:
        return api.get_film(trigger["index"])
    if (
        trigger["type"] == TYPE_EPISODE_TILE
        and show_selection
        and show_selection["season"] is not None
    ):
        return api.get_episode_selection_data(
            show_selection["show"], show_selection["season"], trigger["index"]
        )
    return None


@callback(
    Output(ID_PLAY_REQUEST_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_HERO_RESUME, "n_clicks"),
    Input(ID_HERO_PREV, "n_clicks"),
    Input(ID_HERO_NEXT, "n_clicks"),
    Input({"type": TYPE_FILM_CARD, "index": ALL}, "n_clicks"),
    Input({"type": TYPE_EPISODE_TILE, "index": ALL}, "n_clicks"),
    Input(ID_UP_NEXT_PLAY, "n_clicks"),
    Input(ID_ENDED_STORE, "data"),
    State(ID_USER_STORE, "data"),
    State(ID_SHOW_SELECTION_STORE, "data"),
    State(ID_UP_NEXT_STORE, "data"),
    State(ID_DISMISSED_STORE, "data"),
    State(ID_PLAY_REQUEST_STORE, "data"),
    prevent_initial_call=True,
)
def dispatch_play(*args) -> tuple:
    user, show_selection, up_next, dismissed, play_request = args[-5:]
    trigger = clicked()
    if not trigger or not user:
        return dash.no_update, dash.no_update
    try:
        if trigger == ID_HERO_RESUME:
            return _resume(user), ""
        if trigger in (ID_UP_NEXT_PLAY, ID_ENDED_STORE):
            selection = _queued_episode(up_next, dismissed, play_request)
        else:
            selection = _selection_for(trigger, user, show_selection)
        if selection is None:
            return dash.no_update, dash.no_update
        return _record_and_play(selection, user), ""
    except ApiError:
        return dash.no_update, "The spirits are unwilling: couldn't start playback."


@callback(
    Output(ID_PLAYER, "src"),
    Output(ID_NOW_PLAYING_TITLE, "children"),
    Output(ID_NOW_PLAYING_SUBTITLE, "children"),
    Output(ID_NOW_PLAYING_META, "children"),
    Output(ID_THEATRE, "className"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    prevent_initial_call=True,
)
def render_player(request: dict | None) -> tuple:
    if not request:
        return None, "", "", "", "theatre theatre--idle"
    return (
        request["src"],
        request["title"],
        request["subtitle"],
        request["meta"],
        "theatre",
    )


@callback(
    Output(ID_UP_NEXT_STORE, "data"),
    Input(ID_COUNTDOWN_STORE, "data"),
    State(ID_UP_NEXT_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def prepare_up_next(countdown: dict | None, up_next: dict | None, user: dict | None):
    """Look up the next episode once, when the countdown for a playback begins."""
    if not countdown or not user:
        return dash.no_update
    if up_next and up_next["play_id"] == countdown["play_id"]:
        return dash.no_update
    try:
        selection = api.get_next_episode_selection(user["name"])
        title = f"{get_title(selection)} · {get_episode_label(selection)}"
    except ApiError:
        selection, title = None, ""
    return {"play_id": countdown["play_id"], "selection": selection, "title": title}


@callback(
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_PAUSED_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def record_pause(paused: dict | None, user: dict | None):
    if not paused or not user:
        return dash.no_update
    try:
        api.record_paused(user["id"], paused["file_key"], paused["seconds"])
    except ApiError:
        return "Couldn't remember where you paused."
    return dash.no_update
