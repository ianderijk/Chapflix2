from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask
import dash
import logging
import os
from datetime import datetime
from pathlib import Path
from src.player import Player

player = Player()
logger = logging.getLogger(os.path.join(Path(__name__).parent, "app.log"))
logger.setLevel(logging.INFO)

server = Flask(__name__)
app = dash.Dash(server=server, prevent_initial_callbacks=True)
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
                html.Div(  # div containing the video player
                    children=[
                        dcc.Input(
                            id="VideoProgressInput",
                            type="text",
                            style={"display": "none"},
                        ),
                        dcc.Store(id="VideoProgressStore", storage_type="session"),
                        dcc.Store(id="RedundantOutputStorer", storage_type="session"),
                        # this is only needed because an output element is required for the write_paused_time callback and
                        # i'd rather add a random element than get any deeper into js than i already am.
                        html.Video(controls=True, id="Player", src=None),
                        html.Script("""
                            console.log("Script loaded");
                                document.addEventListener("fullscreenchange", function() {
                                    let video = document.getElementById("Player");
                                    if (document.fullscreenElement && document.fullscreenElement === video) {
                                        video.controls = false;
                                    } else {
                                        video.controls = true;
                                    }
                                });

                                window.addEventListener("load", function() {
                                    let video = document.getElementById("Player");
                                    if (video) {
                                        console.log("Attaching pause handler");
                                        video.addEventListener("pause", function() {
                                            let progress = video.currentTime;
                                            console.log("Paused at:", progress);
                                            let input = document.getElementById("VideoProgressInput");
                                            input.value = progress;
                                            input.dispatchEvent(new Event('input', { bubbles: true }));
                                        });
                                    } else {
                                        console.log("Video element not found at load");
                                    }
                                });
                        """),
                    ],
                    style={
                        "width": "100%",
                        "display": "inline-block",
                        "vertical-align": "bottom",
                        "align": "center",
                    },
                )
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
    Output(component_id="ContinueWatchingText", component_property="children", allow_duplicate=True),
    Input(component_id="users", component_property="value"),
)
def set_user(user: str) -> str:
    if user:
        player.set_user(user)
        return player.get_last_played()
    return ""


@app.callback(
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Output(component_id="ContinueWatchingText", component_property="children", allow_duplicate=True),
    Input(component_id="ContinueWatching", component_property="n_clicks"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def continue_watching(n_clicks: int, user: str) -> tuple[None | str, None | str]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    return player.get_continue_watching()


@app.callback(
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="PreviousEpisode", component_property="n_clicks"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def watch_previous_episode(n_clicks: int, user: str) -> tuple[None | str, None | str]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    return player.get_previous_episode()


@app.callback(
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Output(
        component_id="ContinueWatchingText",
        component_property="children",
        allow_duplicate=True,
    ),
    Input(component_id="NextEpisode", component_property="n_clicks"),
    Input(component_id="users", component_property="value", allow_optional=False),
)
def watch_next_episode(n_clicks: int, user: str) -> tuple[None | str, None | str]:
    if not user:
        return None, None
    elif n_clicks == 0:
        return None, None
    return player.get_next_episode()


@app.callback(
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Input(component_id="FilmPicker", component_property="value"),
    Input(component_id="users", component_property="value"),
)
def play_film(film: str, user: str) -> None | str:
    if not user:
        return None
    elif film == "Pick a film":
        return None
    if film and film != "Pick a film":
        file = player.get_film_path(film)
        return file


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
    Output(component_id="Player", component_property="src", allow_duplicate=True),
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
def play_episode(show: str, season: int, episode: int, user: str) -> tuple[None | str, None | str]:
    if not user:
        return None, None
    elif not show or show == "Pick a show" or not season or not episode:
        return None, None
    file = player.get_show_path(show, season, episode)
    display_string = player.get_last_played()
    return file, display_string


app.clientside_callback(
    """
    function(value) {
        return value;
    }
    """,
    Output(component_id="VideoProgressStore", component_property="data"),
    Input(component_id="VideoProgressInput", component_property="value"),
)


@app.callback(
    Output(
        component_id="RedundantOutputStorer",
        component_property="data",
        allow_duplicate=True,
    ),
    Input(component_id="VideoProgressStore", component_property="data"),
)
def write_pasued_time(pause_time: str) -> None:
    print(pause_time)


if __name__ == "__main__":
    logger.info(f"Starting app at {datetime.now()}")
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
