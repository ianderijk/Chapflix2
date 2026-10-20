import dash
from dash import ALL, Input, Output, State, callback, html

from app.src import api_client as api
from app.src.api_client import ApiError
from app.src.callbacks.triggers import clicked
from app.src.layout import (
    ID_CATALOGUE_STORE,
    ID_FILMS_ROW,
    ID_NOTICE,
    ID_PLAY_REQUEST_STORE,
    ID_SEARCH,
    ID_SHOW_PANEL,
    ID_SHOW_SELECTION_STORE,
    ID_SHOWS_ROW,
    ID_TOP,
    ID_USER_STORE,
    TYPE_FILM_CARD,
    TYPE_SEASON_TAB,
    TYPE_SHOW_CARD,
    build_cards,
    build_show_panel,
)
from app.src.player import pretty_title


@callback(
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


@callback(
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


def _opening_season(show: str, seasons: list[int], user: dict | None) -> int | None:
    """The season the user was last watching in this show, else the first one."""
    if not seasons:
        return None
    if user:
        try:
            last_played = api.get_last_played_selection(user["name"])
            if last_played.get("show") == show and last_played["season"] in seasons:
                return last_played["season"]
        except ApiError:
            pass
    return seasons[0]


@callback(
    Output(ID_SHOW_SELECTION_STORE, "data"),
    Input({"type": TYPE_SHOW_CARD, "index": ALL}, "n_clicks"),
    Input({"type": TYPE_SEASON_TAB, "index": ALL}, "n_clicks"),
    State(ID_SHOW_SELECTION_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def select_show(_shows, _seasons, selection: dict | None, user: dict | None):
    trigger = clicked()
    if not trigger:
        return dash.no_update
    if trigger["type"] == TYPE_SEASON_TAB and selection:
        return {"show": selection["show"], "season": trigger["index"]}
    show = trigger["index"]
    try:
        seasons = api.get_season_options(show)
    except ApiError:
        seasons = []
    return {"show": show, "season": _opening_season(show, seasons, user)}


def _episode_markers(
    show: str, season: int | None, user: dict | None
) -> tuple[int | None, int | None]:
    """Which episode of this season was last watched, and which is up next."""
    last_watched = up_next = None
    if not user:
        return last_watched, up_next
    try:
        last_played = api.get_last_played_selection(user["name"])
        if last_played.get("show") == show and last_played["season"] == season:
            last_watched = last_played["episode"]
        next_episode = api.get_next_episode_selection(user["name"])
        if next_episode["show"] == show and next_episode["season"] == season:
            up_next = next_episode["episode"]
    except ApiError:
        pass
    return last_watched, up_next


@callback(
    Output(ID_SHOW_PANEL, "children"),
    Input(ID_SHOW_SELECTION_STORE, "data"),
    Input(ID_PLAY_REQUEST_STORE, "data"),
    State(ID_USER_STORE, "data"),
    prevent_initial_call=True,
)
def render_show_panel(selection: dict | None, _, user: dict | None):
    if not selection:
        return []
    show, season = selection["show"], selection["season"]
    try:
        seasons = api.get_season_options(show)
        episodes = api.get_episode_options(show, season) if season is not None else []
    except ApiError:
        message = f"Couldn't unearth the episodes of {pretty_title(show)}."
        return [html.P(message, className="empty")]
    last_watched, up_next = _episode_markers(show, season, user)
    return build_show_panel(show, seasons, season, episodes, last_watched, up_next)
