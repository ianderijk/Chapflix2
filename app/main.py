from pathlib import Path

import dash
from flask import send_from_directory

from app.src import config
from app.src.callbacks import billboard, browse, playback, profile
from app.src.layout import build_layout

config.check()

CALLBACK_MODULES = (billboard, browse, playback, profile)

VIDEO_DIR = Path(__file__).parent.parent / "content"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700"
    "&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400"
    "&family=Pirata+One&display=swap"
)

app = dash.Dash(__name__, title="Chapflix", external_stylesheets=[FONTS])
server = app.server
app.layout = build_layout


@server.route("/content/<path:filename>")
def serve_content(filename: Path):
    return send_from_directory(VIDEO_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8042, debug=False, use_reloader=False)
