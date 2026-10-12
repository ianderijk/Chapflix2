import json
import time
from pathlib import Path
from typing import Any

import dash
from dash import ALL, Input, Output, State, ctx, html
from flask import send_from_directory

from app.src import api_client as api
from app.src.api_client import ApiError
from app.src.layout import (
    COUNTDOWN_SECONDS,
    ID_CATALOGUE_STORE,
    ID_COUNTDOWN,
    ID_FILMS_ROW,
    ID_GATE,
    ID_HERO_KICKER,
    ID_HERO_META,
    ID_HERO_NEXT,
    ID_HERO_PREV,
    ID_HERO_RESUME,
    ID_HERO_SUBTITLE,
    ID_HERO_TITLE,
    ID_NOTICE,
    ID_NOW_PLAYING_META,
    ID_NOW_PLAYING_SUBTITLE,
    ID_NOW_PLAYING_TITLE,
    ID_PLAY_REQUEST_STORE,
    ID_PROFILE_NAME,
    ID_REDUNDANT_STORE,
    ID_SEARCH,
    ID_SHOW_PANEL,
    ID_SHOW_SELECTION_STORE,
    ID_SHOWS_ROW,
    ID_SWITCH_PROFILE,
    ID_THEATRE,
    ID_TOP,
    ID_UP_NEXT,
    ID_UP_NEXT_CANCEL,
    ID_UP_NEXT_COUNT,
    ID_UP_NEXT_PLAY,
    ID_UP_NEXT_STORE,
    ID_UP_NEXT_TITLE,
    ID_USER_STORE,
    ID_VIDEO_CONTAINER,
    ID_VIDEO_EVENTS,
    TYPE_EPISODE_TILE,
    TYPE_FILM_CARD,
    TYPE_PROFILE,
    TYPE_SEASON_TAB,
    TYPE_SHOW_CARD,
    build_cards,
    build_layout,
    build_show_panel,
    video_player,
)
from app.src.player import (
    get_file,
    get_play_information,
    get_subtitle,
    get_title,
    is_playable,
    pretty_title,
)

ROOT_DIR = Path(__file__).parent.parent
VIDEO_DIR = ROOT_DIR / "content"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700"
    "&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400"
    "&family=Pirata+One&display=swap"
)

app = dash.Dash(
    __name__,
    title="Chapflix",
    assets_folder=str(ROOT_DIR / "assets"),
    # custom.js has never been loaded by the app (Dash was looking in app/assets),
    # so keep it out to preserve the current fullscreen behaviour
    assets_ignore=r"custom\.js",
    external_stylesheets=[FONTS],
)
server = app.server
app.layout = build_layout


@server.route("/content/<path:filename>")
def serve_content(filename: Path):
    return send_from_directory(VIDEO_DIR, filename)


def _clicked() -> Any:
    """The id of the component that was actually clicked, ignoring components that
    merely appeared in the layout (they trigger callbacks with a falsy n_clicks)."""
    for trigger in ctx.triggered:
        if trigger["value"]:
            prop_id = trigger["prop_id"].rsplit(".", 1)[0]
            return json.loads(prop_id) if prop_id.startswith("{") else prop_id
    return None


def _episode_label(selection: dict[str, Any]) -> str:
    return f"S{selection['season']} E{selection['episode']}"


def _format_seconds(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02}:{secs:02}"
    return f"{minutes}:{secs:02}"


@app.callback(
    Output(ID_USER_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input({"type": TYPE_PROFILE, "index": ALL}, "n_clicks"),
    Input(ID_SWITCH_PROFILE, "n_clicks"),
    prevent_initial_call=True,
)
def choose_profile(*_) -> tuple:
    clicked = _clicked()
    if clicked == ID_SWITCH_PROFILE:
        return None, ""
    if not clicked:
        return dash.no_update, dash.no_update
    name = clicked["index"]
    try:
        return {"name": name, "id": api.get_user_id(name)}, ""
    except ApiError:
        return dash.no_update, f"Couldn't summon {name}'s profile from the API."


@app.callback(
    Output(ID_GATE, "className"),
    Output(ID_PROFILE_NAME, "children"),
    Input(ID_USER_STORE, "modified_timestamp"),
    State(ID_USER_STORE, "data"),
)
def render_profile(_, user: dict | None) -> tuple[str, str]:
    if not user:
        return "gate", ""
    return "gate gate--hidden", user["name"]


@app.callback(
    Output(ID_CATALOGUE_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_USER_STORE, "modified_timestamp"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call="initial_duplicate",
)
def load_catalogue(_, user: dict | None) -> tuple:
    if not user:
        return dash.no_update, dash.no_update
    try:
        catalogue = {
            "shows": api.get_playable_content("shows"),
            "films": api.get_playable_content("films"),
        }
        return catalogue, ""
    except ApiError:
        return dash.no_update, "The vaults are sealed: couldn't load shows and films."


@app.callback(
    Output(ID_SHOWS_ROW, "children"),
    Output(ID_FILMS_ROW, "children"),
    Input(ID_CATALOGUE_STORE, "data"),
    Input(ID_SEARCH, "value"),
    prevent_initial_call=True,
)
def render_rows(catalogue: dict | None, search: str | None) -> tuple:
    if not catalogue:
        return dash.no_update, dash.no_update
    search = (search or "").strip().lower()

    def matches(name: str) -> bool:
        return search in pretty_title(name).lower()

    shows = [show for show in catalogue["shows"] if matches(show)]
    films = [film for film in catalogue["films"] if matches(film)]
    return (
        build_cards(shows, TYPE_SHOW_CARD, f"#{ID_SHOW_PANEL}"),
        build_cards(films, TYPE_FILM_CARD, f"#{ID_TOP}"),
    )


@app.callback(
    Output(ID_SHOW_SELECTION_STORE, "data"),
    Input({"type": TYPE_SHOW_CARD, "index": ALL}, "n_clicks"),
    Input({"type": TYPE_SEASON_TAB, "index": ALL}, "n_clicks"),
    State(ID_SHOW_SELECTION_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def select_show(_shows, _seasons, selection: dict | None, user: dict | None):
    clicked = _clicked()
    if not clicked:
        return dash.no_update
    if clicked["type"] == TYPE_SEASON_TAB and selection:
        return {"show": selection["show"], "season": clicked["index"]}
    show = clicked["index"]
    season = None
    # Open the show on the season the user was last watching, if any
    if user:
        try:
            last_played = api.get_last_played_selection(user["name"])
            if last_played.get("show") == show:
                season = last_played["season"]
        except ApiError:
            pass
    return {"show": show, "season": season}


@app.callback(
    Output(ID_SHOW_PANEL, "children"),
    Input(ID_SHOW_SELECTION_STORE, "data"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def render_show_panel(selection: dict | None, _, user: dict | None):
    if not selection:
        return []
    show = selection["show"]
    try:
        seasons = api.get_season_options(show)
        season = selection["season"] or (seasons[0] if seasons else None)
        episodes = api.get_episode_options(show, season) if season else []
    except ApiError:
        message = f"Couldn't unearth the episodes of {pretty_title(show)}."
        return [html.P(message, className="empty")]

    last_watched = up_next = None
    if user:
        try:
            last_played = api.get_last_played_selection(user["name"])
            if last_played.get("show") == show and last_played["season"] == season:
                last_watched = last_played["episode"]
            next_episode = api.get_next_episode_selection(user["name"])
            if next_episode.get("show") == show and next_episode["season"] == season:
                up_next = next_episode["episode"]
        except ApiError:
            pass
    return build_show_panel(show, seasons, season, episodes, last_watched, up_next)


@app.callback(
    Output(ID_HERO_KICKER, "children"),
    Output(ID_HERO_TITLE, "children"),
    Output(ID_HERO_SUBTITLE, "children"),
    Output(ID_HERO_META, "children"),
    Output(ID_HERO_RESUME, "className"),
    Output(ID_HERO_PREV, "children"),
    Output(ID_HERO_PREV, "className"),
    Output(ID_HERO_NEXT, "children"),
    Output(ID_HERO_NEXT, "className"),
    Input(ID_USER_STORE, "modified_timestamp"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    State(ID_USER_STORE, "data"),
)
def render_billboard(_, __, user: dict | None) -> tuple:
    hidden = "btn btn--hidden"
    if not user:
        return ("", "", "", "", hidden, "", hidden, "", hidden)
    name = user["name"]
    try:
        last_played = api.get_last_played_selection(name)
        seconds = api.get_continue_watching_from(user["id"])
    except ApiError:
        return (
            f"Welcome, {name}",
            "The crypt awaits",
            "Nothing watched yet, or the API is resting. Choose something below.",
            "",
            hidden,
            "",
            hidden,
            "",
            hidden,
        )

    previous_label, previous_class = "", hidden
    next_label, next_class = "", hidden
    if last_played["media_type"] == "show":
        for fetch, arrow, is_next in (
            (api.get_previous_episode_selection, "⏮", False),
            (api.get_next_episode_selection, "⏭", True),
        ):
            try:
                selection = fetch(name)
            except ApiError:
                continue
            if not is_playable(selection):
                continue
            label = f"{arrow} {_episode_label(selection)}"
            if is_next:
                next_label, next_class = label, "btn btn--ghost"
            else:
                previous_label, previous_class = label, "btn btn--ghost"

    meta = get_play_information(last_played)
    if seconds:
        meta += f" | Paused at {_format_seconds(seconds)}"
    return (
        f"Continue watching, {name}",
        get_title(last_played),
        get_subtitle(last_played),
        meta,
        "btn btn--blood",
        previous_label,
        previous_class,
        next_label,
        next_class,
    )


def _play_request(selection: dict[str, Any], start_at: float = 0) -> dict[str, Any]:
    file = str(get_file(selection))
    if start_at:
        file = f"{file}#t={start_at}"
    return {
        "file": file,
        "title": get_title(selection),
        "subtitle": get_subtitle(selection),
        "meta": get_play_information(selection),
        "requested_at": time.time(),
    }


@app.callback(
    Output(ID_PLAY_REQUEST_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_HERO_RESUME, "n_clicks"),
    Input(ID_HERO_PREV, "n_clicks"),
    Input(ID_HERO_NEXT, "n_clicks"),
    Input({"type": TYPE_FILM_CARD, "index": ALL}, "n_clicks"),
    Input({"type": TYPE_EPISODE_TILE, "index": ALL}, "n_clicks"),
    Input(ID_UP_NEXT_PLAY, "n_clicks"),
    Input(ID_COUNTDOWN, "n_intervals"),
    State(ID_USER_STORE, "data"),
    State(ID_SHOW_SELECTION_STORE, "data"),
    State(ID_UP_NEXT_STORE, "data"),
    prevent_initial_call=True,
)
def dispatch_play(*args) -> tuple:
    user, show_selection, up_next = args[-3:]
    clicked = _clicked()
    if not clicked or not user:
        return dash.no_update, dash.no_update
    name = user["name"]
    try:
        if clicked == ID_HERO_RESUME:
            last_played = api.get_last_played_selection(name)
            seconds = api.get_continue_watching_from(user["id"])
            return _play_request(last_played, seconds), ""

        if clicked in (ID_HERO_PREV, ID_HERO_NEXT):
            fetch = (
                api.get_previous_episode_selection
                if clicked == ID_HERO_PREV
                else api.get_next_episode_selection
            )
            selection = fetch(name)
            if not is_playable(selection):
                return dash.no_update, "There's no episode that way."
            return _play_request(selection), ""

        if clicked in (ID_UP_NEXT_PLAY, ID_COUNTDOWN):
            if not up_next or not up_next["active"]:
                return dash.no_update, dash.no_update
            elapsed = ctx.inputs[f"{ID_COUNTDOWN}.n_intervals"] - up_next["started_at"]
            if clicked == ID_COUNTDOWN and elapsed != COUNTDOWN_SECONDS:
                return dash.no_update, dash.no_update
            selection = up_next["selection"]
        elif clicked["type"] == TYPE_FILM_CARD:
            selection = api.get_film(clicked["index"])
        elif clicked["type"] == TYPE_EPISODE_TILE and show_selection:
            selection = api.get_episode_selection_data(
                show_selection["show"], show_selection["season"], clicked["index"]
            )
        else:
            return dash.no_update, dash.no_update

        api.record_watched(selection, user["id"])
        return _play_request(selection), ""
    except ApiError:
        return dash.no_update, "The spirits are unwilling: couldn't start playback."


@app.callback(
    Output(ID_VIDEO_CONTAINER, "children"),
    Output(ID_NOW_PLAYING_TITLE, "children"),
    Output(ID_NOW_PLAYING_SUBTITLE, "children"),
    Output(ID_NOW_PLAYING_META, "children"),
    Output(ID_THEATRE, "className"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    prevent_initial_call=True,
)
def render_player(request: dict | None) -> tuple:
    if not request:
        return video_player(None), "", "", "", "theatre theatre--idle"
    return (
        video_player(request["file"]),
        request["title"],
        request["subtitle"],
        request["meta"],
        "theatre",
    )


@app.callback(
    Output(ID_UP_NEXT_STORE, "data"),
    Output(ID_UP_NEXT, "className"),
    Output(ID_UP_NEXT_TITLE, "children"),
    Output(ID_UP_NEXT_COUNT, "children"),
    Output(ID_COUNTDOWN, "disabled"),
    Input(ID_VIDEO_EVENTS, "event"),
    Input(ID_UP_NEXT_PLAY, "n_clicks"),
    Input(ID_UP_NEXT_CANCEL, "n_clicks"),
    Input(ID_COUNTDOWN, "n_intervals"),
    State(ID_USER_STORE, "data"),
    State(ID_UP_NEXT_STORE, "data"),
    prevent_initial_call=True,
)
def up_next_countdown(
    event: dict | None, _, __, n_intervals: int | None, user: dict | None, up_next
) -> tuple:
    hide = ({"active": False}, "up-next", "", "", True)
    unchanged = (dash.no_update,) * 5
    trigger = ctx.triggered_id

    if trigger == ID_COUNTDOWN:
        if not up_next or not up_next["active"]:
            return unchanged
        remaining = COUNTDOWN_SECONDS - ((n_intervals or 0) - up_next["started_at"])
        if remaining <= 0:
            return hide
        return (dash.no_update,) * 3 + (f"Starting in {remaining}…", dash.no_update)

    if trigger in (ID_UP_NEXT_PLAY, ID_UP_NEXT_CANCEL):
        return hide

    if not event or not user:
        return unchanged
    if event.get("type") == "loadedmetadata":
        return hide
    if event.get("type") != "ended":
        return unchanged

    # Films don't autoplay anything afterwards
    try:
        if api.get_last_played_selection(user["name"])["media_type"] == "film":
            return hide
        selection = api.get_next_episode_selection(user["name"])
    except ApiError:
        return hide
    if not is_playable(selection):
        return hide
    return (
        {"active": True, "selection": selection, "started_at": n_intervals or 0},
        "up-next up-next--visible",
        f"{get_title(selection)} · {_episode_label(selection)}",
        f"Starting in {COUNTDOWN_SECONDS}…",
        False,
    )


@app.callback(
    Output(ID_REDUNDANT_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input(ID_VIDEO_EVENTS, "n_events"),
    State(ID_VIDEO_EVENTS, "event"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def write_paused_time(_, event: dict | None, user: dict | None) -> tuple:
    if not user or not event or "target.currentTime" not in event:
        return dash.no_update, dash.no_update
    try:
        api.record_paused(user["id"], event["target.currentTime"])
    except ApiError:
        return dash.no_update, "Couldn't remember where you paused."
    return dash.no_update, dash.no_update


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
