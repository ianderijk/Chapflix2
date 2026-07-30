from dash import dcc, html, State
from dash_extensions import EventListener
from dash.dependencies import Input, Output
from flask import send_from_directory
from typing import cast, Literal, Any
from pathlib import Path
import dash
import requests
import json
from app.src.player import drop_down_lists, get_file, get_display_string


def get_endpoint_url(endpoint: str) -> str:
    return "http://127.0.0.1:8000/" + endpoint


def get_user_id(user: str) -> int:
    url = get_endpoint_url(f"user/{user}")
    response = requests.get(url)
    data = json.loads(response.text)
    return data["id_"]


def record_watched(data: dict):
    url = get_endpoint_url("record-play")
    response = requests.post(url=url, data=data)
    return response


def get_playable_content(
    content_type: Literal["shows", "films"],
) -> list[dict[str, str]]:
    url = get_endpoint_url(content_type)
    response = requests.get(url)
    data = json.loads(response.text)
    options = data[content_type]
    return drop_down_lists(options)


def get_season_options(show: str) -> list[int]:
    url = get_endpoint_url(f"{show}/seasons")
    response = requests.get(url)
    data = json.loads(response.text)
    options = data["seasons"]
    return options


def get_episode_options(show: str, season: int) -> list[int]:
    url = get_endpoint_url(f"{show}/{season}")
    response = requests.get(url)
    data = json.loads(response.text)
    options = data["episodes"]
    return options


def get_episode_selection_data(show: str, season: int, episode: int) -> dict[str, Any]:
    url = get_endpoint_url(f"{show}/{season}/{episode}")
    response = requests.get(url)
    data = json.loads(response.text)
    return data


def get_film(film: str) -> dict[str, Any] | None:
    if film == "Pick a film" or film == "":
        return
    url = get_endpoint_url(f"film/{film}")
    response = requests.get(url)
    data = json.loads(response.text)
    return data


def get_next_episode_selection(user: str) -> dict[str, Any]:
    url = get_endpoint_url(f"user/{user}/next-episode")
    response = requests.get(url)
    data = json.loads(response.text)
    return data


def get_previous_episode_selection(user: str) -> dict[str, Any]:
    url = get_endpoint_url(f"user/{user}/previous-episode")
    response = requests.get(url)
    data = json.loads(response.text)
    return data


def get_last_played_selection(user: str) -> dict[str, Any]:
    url = get_endpoint_url(f"user/{user}/last-played")
    response = requests.get(url)
    data = json.loads(response.text)
    return data


def get_continue_watching_from(user: str) -> float:
    url = get_endpoint_url(f"get-paused/{user}")
    response = requests.get(url)
    data = json.loads(response.text)
    seconds = data["seconds"]
    return seconds


ID_USERS = "users"
ID_CONTINUE_TEXT = "ContinueWatchingText"
ID_CONTINUE_BTN = "ContinueWatching"
ID_PREV_TEXT = "PreviousEpisodeText"
ID_PREV_BTN = "PreviousEpisode"
ID_NEXT_TEXT = "NextEpisodeText"
ID_NEXT_BTN = "NextEpisode"
ID_FILM_PICKER = "FilmPicker"
ID_SHOW_PICKER = "ShowPicker"
ID_SEASON_PICKER = "SeasonPicker"
ID_EPISODE_PICKER = "EpisodePicker"
ID_VIDEO_CONTAINER = "VideoContainer"
ID_VIDEO_EVENTS = "VideoEvents"
ID_REDUNDANT_STORE = "RedundantOutputStore"
ID_PLAYER = "Player"


def default_event_listener(file: Path | str | None) -> EventListener | None:
    if not file:
        return
    return EventListener(
        id="VideoEvents",
        events=[
            {"event": "pause", "props": ["target.currentTime"]},
            {"event": "loadedmetadata"},
            {"event": "ended", "props": ["type"]},
        ],
        logging=True,
        children=[
            html.Video(
                controls=True,
                id=ID_PLAYER,
                src=str(file),
                autoPlay=True,
            ),
        ],
    )


VIDEO_DIR = Path(__file__).parent.parent / "content"
app = dash.Dash(__name__, prevent_initial_callbacks=True)
server = app.server


@server.route("/content/<path:filename>")
def serve_content(filename: Path):
    return send_from_directory(VIDEO_DIR, filename)


# Styles
COMMON_STYLE = {
    "width": "100%",
    "display": "inline-block",
    "vertical-align": "top",
    "align": "center",
}
VIDEO_CONTAINER_STYLE = {
    "width": "100%",
    "display": "inline-block",
    "vertical-align": "bottom",
    "align": "center",
}


def build_user_controls() -> html.Div:
    return html.Div(
        children=[
            html.H2("Welcome to Chapflix"),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Dropdown(
                                id=ID_USERS,
                                options=[
                                    {"label": "Lady", "value": "Lady"},
                                    {"label": "Chap", "value": "Chap"},
                                ],
                                placeholder="Pick a user",
                                searchable=False,
                            )
                        ]
                    ),
                    html.Div(
                        children=[
                            dcc.Markdown(id=ID_CONTINUE_TEXT, children=None),
                            html.Button(
                                "Continue watching", id=ID_CONTINUE_BTN, n_clicks=0
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            dcc.Markdown(id=ID_PREV_TEXT, children=""),
                            html.Button("Previous episode", id=ID_PREV_BTN, n_clicks=0),
                        ]
                    ),
                    html.Div(
                        children=[
                            dcc.Markdown(id=ID_NEXT_TEXT, children=None),
                            html.Button("Next episode", id=ID_NEXT_BTN, n_clicks=0),
                        ]
                    ),
                ]
            ),
        ],
        style=COMMON_STYLE,
    )


def build_film_picker() -> html.Div:
    return html.Div(
        children=[
            html.H5("Films"),
            dcc.Dropdown(
                id=ID_FILM_PICKER,
                options=cast(list, get_playable_content("films")),
                placeholder="Pick a film",
                value="Pick a film",
                searchable=False,
            ),
        ]
    )


def build_show_picker() -> html.Div:
    return html.Div(
        children=[
            html.H5("TV Shows"),
            dcc.Dropdown(
                id=ID_SHOW_PICKER,
                options=cast(list, get_playable_content("shows")),
                value="Pick a show",
                placeholder="Pick a show",
                searchable=False,
            ),
            dcc.Dropdown(id=ID_SEASON_PICKER, options=[], value=None, searchable=False),
            dcc.Dropdown(
                id=ID_EPISODE_PICKER, options=[], value=None, searchable=False
            ),
        ]
    )


def build_top_controls() -> html.Div:
    return html.Div(
        children=[
            html.Div(
                children=[
                    build_user_controls(),
                    build_film_picker(),
                    build_show_picker(),
                ],
                style=COMMON_STYLE,
            )
        ],
        style=COMMON_STYLE,
    )


def build_video_container() -> html.Div:
    return html.Div(
        children=[
            html.Script(src="/assets/custom.js"),
            EventListener(id=ID_VIDEO_EVENTS),
            dcc.Store(id=ID_REDUNDANT_STORE, storage_type="session"),
            html.Div(id=ID_VIDEO_CONTAINER),
        ],
        style=VIDEO_CONTAINER_STYLE,
    )


def build_layout() -> html.Div:
    return html.Div(children=[build_top_controls(), build_video_container()])


app.layout = build_layout()


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_VIDEO_EVENTS, component_property="event"),
    Input(component_id=ID_USERS, component_property="value", allow_optional=False),
    prevent_initial_call=True,
)
def autoplay_next_episode(
    event: EventListener,
    user: str,
) -> tuple[EventListener | dash.NoUpdate | None, str | dash.NoUpdate | None]:
    if event and event["type"] == "ended":
        selection = get_next_episode_selection(user)
        last_played = get_last_played_selection(user)
        if last_played["media_type"] == "film":
            return dash.no_update, dash.no_update
        file = get_file(selection)
        display_string = get_display_string(selection, "show")
        user_id = get_user_id(user)
        watched = {
            "film": None,
            "show": selection["show"],
            "season": selection["season"],
            "episode": selection["episode"],
            "user_id": user_id,
            "file_key": selection["file_key"],
        }
        record_watched(watched)
        return default_event_listener(file), display_string
    return dash.no_update, dash.no_update


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_CONTINUE_BTN, component_property="n_clicks"),
    State(component_id=ID_USERS, component_property="value"),
)
def continue_watching(
    n_clicks: int, user: str
) -> tuple[None | EventListener, str | None]:
    if n_clicks == 0 or not user:
        return None, None
    last_played = get_last_played_selection(user)
    file = get_file(last_played)
    content_type = last_played["media_type"]
    display_string = get_display_string(last_played, content_type)
    seconds = get_continue_watching_from(user)
    file = f"{file}#t={seconds}"
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_PREV_BTN, component_property="n_clicks"),
    State(component_id=ID_USERS, component_property="value", allow_optional=False),
)
def watch_previous_episode(
    n_clicks: int, user: str
) -> tuple[None | EventListener, None | str]:
    if n_clicks == 0 or not user:
        return None, None
    previous_episode_data = get_previous_episode_selection(user)
    file = get_file(previous_episode_data)
    display_string = get_display_string(previous_episode_data, "show")
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_NEXT_BTN, component_property="n_clicks"),
    State(component_id=ID_USERS, component_property="value", allow_optional=False),
)
def watch_next_episode(
    n_clicks: int, user: str
) -> tuple[None | EventListener, None | str]:
    if n_clicks == 0 or not user:
        return None, None
    next_episode_data = get_next_episode_selection(user)
    file = get_file(next_episode_data)
    display_string = get_display_string(next_episode_data, "show")
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_FILM_PICKER, component_property="value"),
    State(component_id=ID_USERS, component_property="value"),
)
def play_film(film: str, user: str) -> tuple[None | EventListener, None | str]:
    if film == "Pick a film" or not user:
        return None, None
    selection = get_film(film)
    if selection is None:
        return None, None
    file = get_file(selection)
    display_string = get_display_string(selection, "film")
    user_id = get_user_id(user)
    watched = {
        "film": selection["film"],
        "show": None,
        "season": None,
        "episode": None,
        "user_id": user_id,
        "file_key": selection["file_key"],
    }
    record_watched(watched)
    return default_event_listener(file), display_string


@app.callback(
    Output(component_id=ID_SEASON_PICKER, component_property="options"),
    Output(component_id=ID_SEASON_PICKER, component_property="value"),
    Input(component_id=ID_SHOW_PICKER, component_property="value"),
)
def update_seasons(show: str) -> tuple:
    if show and show != "Pick a show":
        return get_season_options(show), None
    return [], None


@app.callback(
    Output(component_id=ID_EPISODE_PICKER, component_property="options"),
    Output(component_id=ID_EPISODE_PICKER, component_property="value"),
    Input(component_id=ID_SHOW_PICKER, component_property="value"),
    Input(component_id=ID_SEASON_PICKER, component_property="value"),
)
def update_episodes(show: str, season: int) -> tuple:
    if show and season:
        return get_episode_options(show, season), None
    return [], None


@app.callback(
    Output(
        component_id=ID_VIDEO_CONTAINER,
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id=ID_CONTINUE_TEXT,
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id=ID_SHOW_PICKER, component_property="value"),
    Input(component_id=ID_SEASON_PICKER, component_property="value"),
    Input(component_id=ID_EPISODE_PICKER, component_property="value"),
    State(component_id=ID_USERS, component_property="value", allow_optional=False),
)
def play_episode(
    show: str, season: int, episode: int, user: str
) -> tuple[None | EventListener, None | str]:
    if not user:
        return None, None
    elif not show or show == "Pick a show" or not season or not episode:
        return None, None
    selection = get_episode_selection_data(show, season, episode)
    file = get_file(selection)
    display_string = get_display_string(selection, "show")
    user_id = get_user_id(user)
    watched = {
        "film": None,
        "show": selection["show"],
        "season": selection["season"],
        "episode": selection["episode"],
        "user_id": user_id,
        "file_key": selection["file_key"],
    }
    record_watched(watched)
    return default_event_listener(file), display_string


@app.callback(
    Output(component_id=ID_REDUNDANT_STORE, component_property="data"),
    Input(component_id=ID_VIDEO_EVENTS, component_property="n_events"),
    State(component_id=ID_VIDEO_EVENTS, component_property="event"),
    State(component_id=ID_USERS, component_property="value"),
    suppress_callback_exceptions=True,
    prevent_initial_callback=True,
)
def write_paused_time(_, data: dict[str, float], user: str) -> None:
    if data and "target.currentTime" in data:
        user_id = get_user_id(user)
        seconds = data["target.currentTime"]
        data = {"user_id": user_id, "video_progress": seconds}
        url = get_endpoint_url("record-paused")
        requests.post(url=url, data=data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
