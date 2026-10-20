import dash
from dash import ALL, Input, Output, State, callback

from app.src import api_client as api
from app.src.api_client import ApiError
from app.src.callbacks.triggers import clicked
from app.src.layout import (
    ID_GATE,
    ID_NOTICE,
    ID_PROFILE_NAME,
    ID_SWITCH_PROFILE,
    ID_USER_STORE,
    TYPE_PROFILE,
)


@callback(
    Output(ID_USER_STORE, "data"),
    Output(ID_NOTICE, "children", allow_duplicate=True),
    Input({"type": TYPE_PROFILE, "index": ALL}, "n_clicks"),
    Input(ID_SWITCH_PROFILE, "n_clicks"),
    prevent_initial_call=True,
)
def choose_profile(*_) -> tuple:
    trigger = clicked()
    if trigger == ID_SWITCH_PROFILE:
        return None, ""
    if not trigger:
        return dash.no_update, dash.no_update
    name = trigger["index"]
    try:
        return {"name": name, "id": api.get_user_id(name)}, ""
    except ApiError:
        return dash.no_update, f"Couldn't summon {name}'s profile from the API."


@callback(
    Output(ID_GATE, "className"),
    Output(ID_PROFILE_NAME, "children"),
    Input(ID_USER_STORE, "modified_timestamp"),
    State(ID_USER_STORE, "data"),
)
def render_profile(_, user: dict | None) -> tuple[str, str]:
    if not user:
        return "gate", ""
    return "gate gate--hidden", user["name"]
