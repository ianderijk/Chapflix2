from typing import Any, Callable

import dash
from dash import Input, Output, State, callback

from app.src import api_client as api
from app.src.api_client import ApiError
from app.src.layout import (
    ID_HERO_KICKER,
    ID_HERO_META,
    ID_HERO_NEXT,
    ID_HERO_PREV,
    ID_HERO_RESUME,
    ID_HERO_SUBTITLE,
    ID_HERO_TITLE,
    ID_NOTICE,
    ID_PLAY_REQUEST_STORE,
    ID_USER_STORE,
)
from app.src.player import (
    format_seconds,
    get_episode_label,
    get_play_information,
    get_subtitle,
    get_title,
)

HIDDEN = "btn btn--hidden"
GHOST = "btn btn--ghost"
PRIMARY = "btn btn--blood"


def _neighbour_button(
    fetch: Callable[[str], dict[str, Any] | None], arrow: str, name: str
) -> tuple[str, str]:
    """Label and class for the previous/next episode button, hidden if there's none."""
    selection = fetch(name)
    if selection is None:
        return "", HIDDEN
    return f"{arrow} {get_episode_label(selection)}", GHOST


def _neighbour_buttons(last_played: dict[str, Any], name: str) -> tuple[str, ...]:
    if last_played["media_type"] != "show":
        return ("", HIDDEN, "", HIDDEN)
    return (
        *_neighbour_button(api.get_previous_episode_selection, "⏮", name),
        *_neighbour_button(api.get_next_episode_selection, "⏭", name),
    )


def _empty_billboard(name: str) -> tuple:
    return (
        f"Welcome, {name}",
        "The crypt awaits",
        "Nothing watched yet, or the API is resting. Choose something below.",
        "",
        HIDDEN,
        "",
        HIDDEN,
        "",
        HIDDEN,
        dash.no_update,
    )


@callback(
    Output(ID_HERO_KICKER, "children"),
    Output(ID_HERO_TITLE, "children"),
    Output(ID_HERO_SUBTITLE, "children"),
    Output(ID_HERO_META, "children"),
    Output(ID_HERO_RESUME, "className"),
    Output(ID_HERO_PREV, "children"),
    Output(ID_HERO_PREV, "className"),
    Output(ID_HERO_NEXT, "children"),
    Output(ID_HERO_NEXT, "className"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_USER_STORE, "modified_timestamp"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call="initial_duplicate",
)
def render_billboard(_, __, user: dict | None) -> tuple:
    if not user:
        return ("", "", "", "", HIDDEN, "", HIDDEN, "", HIDDEN, dash.no_update)
    name = user["name"]
    try:
        last_played = api.get_last_played_selection(name)
        seconds = api.get_continue_watching_from(user["id"], last_played["file_key"])
    except ApiError:
        return _empty_billboard(name)

    try:
        neighbours, notice = _neighbour_buttons(last_played, name), dash.no_update
    except ApiError:
        neighbours = ("", HIDDEN, "", HIDDEN)
        notice = "Couldn't find the neighbouring episodes."

    meta = get_play_information(last_played)
    if seconds:
        meta += f" | Paused at {format_seconds(seconds)}"
    return (
        f"Continue watching, {name}",
        get_title(last_played),
        get_subtitle(last_played),
        meta,
        PRIMARY,
        *neighbours,
        notice,
    )
