from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask
import dash
from src.player import Player

player = Player()

server = Flask(__name__)
app = dash.Dash(server=server, prevent_initial_callbacks=True)
app.layout = html.Div(  # outer most div, whole page
    children=[
        html.Div(  # big div at the top used for menus
            children=[
                html.Div(  # div containing the dropdowns
                    children=[
                        html.H2("Welcome to Chapflix"),
                        html.Button("Next episode", id="AutoPlayNext", n_clicks=0),
                        dcc.Markdown(id="LastPlayedHeader", children=player.last_played_name),
                        html.H5("Films"),
                        dcc.Dropdown(
                            id="FilmPicker",
                            options=player.playable_films,
                            value="Pick a film",
                        ),
                        html.H5("TV Shows"),
                        dcc.Dropdown(
                            id="ShowPicker",
                            options=player.playable_shows,
                            value="Pick a show",
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
                        html.Video(controls=True, id="Player", src=None),
                        html.Script("""
                    document.addEventListener("fullscreenchange", function() {
                                let video = document.getElementById("Player");
                                if (document.fullscreenElement && document.fullscreenElement === video) {
                                    video.controls = false;
                                } else {
                                    video.controls = true;
                                }
                            });"""),
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
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Input(component_id="AutoPlayNext", component_property="n_clicks"),
)
def play_from_last(n_clicks: int) -> None | str:
    if n_clicks == 0:
        return
    return player.next_episode


@app.callback(
    Output(component_id="Player", component_property="src", allow_duplicate=True),
    Input(component_id="FilmPicker", component_property="value"),
)
def play_film(film: str) -> None | str:
    if film == "Pick a film":
        return None
    if film and film != "Pick a film":
        file = player.get_film_path(film)
        return file


@app.callback(
    Output(
        component_id="LastPlayedHeader",
        component_property="value",
        allow_duplicate=True,
    ),
    Output(component_id="SeasonPicker", component_property="options"),
    Output(component_id="SeasonPicker", component_property="value"),
    Input(component_id="ShowPicker", component_property="value"),
)
def update_seasons(show: str) -> tuple:
    if show and show != "Pick a show":
        return (
            player.get_selection_last_played(show),
            player.get_season_options(show),
            None,
        )
    return player.last_played_name, [], None


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
    Input(component_id="ShowPicker", component_property="value"),
    Input(component_id="SeasonPicker", component_property="value"),
    Input(component_id="EpisodePicker", component_property="value"),
)
def play_episode(show: str, season: int, episode: int) -> None | str:
    if not show or show == "Pick a show" or not season or not episode:
        return
    file = player.get_show_path(show, season, episode)
    return file


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
