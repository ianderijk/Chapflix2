from dash import dcc, html, State
from dash_extensions import EventListener
from dash.dependencies import Input, Output
from flask import send_from_directory
import dash
from pathlib import Path
from app.src.player import Player, format_auto_play_string
from app.src.logger import (
    log_app_starting,
    log_user_selection,
    log_file_played,
    log_file_paused,
)

player = Player()


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
                id="Player",
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


# Component IDs
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


def build_film_picker(player: "Player") -> html.Div:
    return html.Div(
        children=[
            html.H5("Films"),
            dcc.Dropdown(
                id=ID_FILM_PICKER,
                options=player.playable_films,
                placeholder="Pick a film",
                value="Pick a film",
                searchable=False,
            ),
        ]
    )


def build_show_picker(player: "Player") -> html.Div:
    return html.Div(
        children=[
            html.H5("TV Shows"),
            dcc.Dropdown(
                id=ID_SHOW_PICKER,
                options=player.playable_shows,
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


def build_top_controls(player: "Player") -> html.Div:
    return html.Div(
        children=[
            html.Div(
                children=[
                    build_user_controls(),
                    build_film_picker(player),
                    build_show_picker(player),
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


def build_layout(player: "Player") -> html.Div:
    return html.Div(children=[build_top_controls(player), build_video_container()])


app.layout = build_layout(player)


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="VideoEvents", component_property="event"),
    prevent_initial_call=True,
)
def autoplay_next_episode(
    event: EventListener,
) -> tuple[EventListener | dash.NoUpdate | None, str | dash.NoUpdate | None]:
    if event and event["type"] == "ended":
        file, display_string = player.get_next_episode()
        log_file_played(player, "auto_play_next_episode")
        return default_event_listener(file), display_string
    return dash.no_update, dash.no_update


@app.callback(
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="users", component_property="value"),
)
def set_user(user: str) -> str:
    if user:
        player.user = user
        log_user_selection(player)
        player.last_played = player.user
        return player.get_last_played_string()
    return ""


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="ContinueWatching", component_property="n_clicks"),
    State(component_id="users", component_property="value"),
)
def continue_watching(
    n_clicks: int, user: str
) -> tuple[None | EventListener, str | None]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    file, display_string = player.get_continue_watching()
    seconds = player.get_continue_watching_from()
    file = f"{file}#t={seconds}"
    log_file_played(player, "continue_watching")
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="PreviousEpisode", component_property="n_clicks"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def watch_previous_episode(
    n_clicks: int, user: str
) -> tuple[None | EventListener, None | str]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    file, display_string = player.get_previous_episode()
    log_file_played(player, "watch_previous_episode")
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="NextEpisode", component_property="n_clicks"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def watch_next_episode(
    n_clicks: int, user: str
) -> tuple[None | EventListener, None | str]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    file, display_string = player.get_next_episode()
    log_file_played(player, "watch_next_episode")
    return default_event_listener(file), display_string


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="FilmPicker", component_property="value"),
    Input(component_id="users", component_property="value"),
)
def play_film(film: str, user: str) -> None | EventListener:
    if not user:
        return None
    elif film == "Pick a film":
        return None
    if film and film != "Pick a film":
        file = player.get_film_path(film)
        log_file_played(player, "play_film")
        return default_event_listener(file)


@app.callback(
    Output(component_id="SeasonPicker", component_property="options"),
    Output(component_id="SeasonPicker", component_property="value"),
    Input(component_id="ShowPicker", component_property="value"),
)
def update_seasons(show: str) -> tuple:
    if show and show != "Pick a show":
        return (
            player.get_season_options(show),
            None,
        )
    return [], None


@app.callback(
    Output(component_id="EpisodePicker", component_property="options"),
    Output(component_id="EpisodePicker", component_property="value"),
    Input(component_id="ShowPicker", component_property="value"),
    Input(component_id="SeasonPicker", component_property="value"),
)
def update_episodes(show: str, season: int) -> tuple:
    if show and season:
        return player.get_episode_options(show, season), None
    return [], None


@app.callback(
    Output(
        component_id="VideoContainer",
        component_property="children",
        allow_duplicate=True,
    ),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="ShowPicker", component_property="value"),
    Input(component_id="SeasonPicker", component_property="value"),
    Input(component_id="EpisodePicker", component_property="value"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def play_episode(
    show: str, season: int, episode: int, user: str
) -> tuple[None | EventListener, None | str]:
    if not user:
        return None, None
    elif not show or show == "Pick a show" or not season or not episode:
        return None, None
    file = player.get_show_path(show, season, episode)
    display_string = format_auto_play_string(player.last_played)
    log_file_played(player, "play_episode")
    return default_event_listener(file), display_string


@app.callback(
    Output(component_id="RedundantOutputStore", component_property="data"),
    Input(component_id="VideoEvents", component_property="n_events"),
    State(component_id="VideoEvents", component_property="event"),
    suppress_callback_exceptions=True,
    prevent_initial_callback=True,
)
def write_paused_time(_, data: dict[str, float]) -> None:
    if data and "target.currentTime" in data.keys():
        seconds = data["target.currentTime"]
        player.record_paused_file(seconds)
        log_file_paused(player)


if __name__ == "__main__":
    log_app_starting()
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
