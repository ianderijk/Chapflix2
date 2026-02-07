from dash import dcc, html, State
from dash_extensions import EventListener
from dash.dependencies import Input, Output
from flask import Flask
import dash
import os
from pathlib import Path
from src.player import Player
from src.logger import log_app_starting, log_user_selection, log_file_played, log_file_paused

player = Player()


def default_event_listener(file: str | None) -> EventListener | None:
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
                src=file,
                autoPlay=True,
            ),
        ],
    )


server = Flask(__name__)
app = dash.Dash(server=server, prevent_initial_callbacks=True, )
app.layout = html.Div(  # outer most div, whole page
    children=[
        html.Div(  # big div at the top used for menus
            children=[
                html.Div(  # div containing the dropdowns
                    children=[
                        html.H2("Welcome to Chapflix"),
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            id="users",
                                            options=[
                                                {"label": "Lady", "value": "Lady"},
                                                {"label": "Chap", "value": "Chap"},
                                            ],
                                            placeholder="Pick a user",
                                        )
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        dcc.Markdown(
                                            id="ContinueWatchingText",
                                            children=None,
                                        ),
                                        html.Button(
                                            "Continue watching",
                                            id="ContinueWatching",
                                            n_clicks=0,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        dcc.Markdown(
                                            id="PreviousEpisodeText", children=""
                                        ),
                                        html.Button(
                                            "Previous episode",
                                            id="PreviousEpisode",
                                            n_clicks=0,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        dcc.Markdown(
                                            id="NextEpisodeText", children=None
                                        ),
                                        html.Button(
                                            "Next episode", id="NextEpisode", n_clicks=0
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        html.H5("Films"),
                        dcc.Dropdown(
                            id="FilmPicker",
                            options=player.playable_films,
                            placeholder="Pick a film",
                            value="Pick a film",
                        ),
                        html.H5("TV Shows"),
                        dcc.Dropdown(
                            id="ShowPicker",
                            options=player.playable_shows,
                            value="Pick a show",
                            placeholder="Pick a show",
                        ),
                        dcc.Dropdown(id="SeasonPicker", options=[], value=None),
                        dcc.Dropdown(id="EpisodePicker", options=[], value=None),
                    ],
                    style={
                        "width": "100%",
                        "display": "inline-block",
                        "vertical-align": "top",
                        "align": "center",
                    },
                )
            ],
            style={
                "width": "100%",
                "display": "inline-block",
                "vertical-align": "top",
                "align": "center",
            },
        ),
        html.Div(  # div container for the video player
            children=[
                html.Script(src="/assets/custom.js"),
                EventListener(id="VideoEvents"),
                dcc.Store(id="RedundantOutputStore", storage_type="session"),
                html.Div(
                    id="VideoContainer",
                ),
            ],
            style={
                "width": "100%",
                "display": "inline-block",
                "vertical-align": "bottom",
                "align": "center",
            },
        ),
    ]
)


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
    prevent_intial_call=True,
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
        player.set_user(user)
        log_user_selection(player)
        return player.get_last_played()
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
    display_string = player.get_last_played()
    log_file_played(player, "play_episode")
    return default_event_listener(file), display_string


@app.callback(
    Output(component_id="RedundantOutputStore", component_property="data"),
    Input(component_id="VideoEvents", component_property="n_events"),
    State(component_id="VideoEvents", component_property="event"),
    suppress_callback_exceptions=True,
    prevent_initial_callback=True,
)
def write_pasued_time(_, data: dict[str, float]) -> None:
    if data and "target.currentTime" in data.keys():
        seconds = data["target.currentTime"]
        player.record_paused_file(seconds)
        log_file_paused(player)


if __name__ == "__main__":
    log_app_starting()
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
