import json
from typing import Any

from dash import ctx


def clicked() -> Any:
    """The id of the input that actually fired.

    Components that have just been rendered also trigger callbacks, but with an
    empty value, so the first trigger carrying a value is the real one.
    """
    for trigger in ctx.triggered:
        if trigger["value"]:
            prop_id = trigger["prop_id"].rsplit(".", 1)[0]
            return json.loads(prop_id) if prop_id.startswith("{") else prop_id
    return None
