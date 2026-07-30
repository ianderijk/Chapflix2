from fastapi import FastAPI, Depends, HTTPException
from typing import Any
from datetime import datetime
from utils.dbutils import execute_statement
from api.app.models.user import User
from api.app.models.events import Watched, PausedPlay
import api.app.service.service as service


app = FastAPI()


def _get_current_user(name: str) -> User:
    user = service.get_user(name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{name}' not found")
    return user


@app.get("/user/{name}")
async def get_user_endpoint(user: User = Depends(_get_current_user)) -> dict[str, Any]:
    return user.model_dump()


@app.get("/user/{name}/last-played")
async def get_last_played(user: User = Depends(_get_current_user)) -> dict[str, Any]:
    last_played = service.get_last_played(user)
    return last_played.model_dump()


@app.get("/user/{name}/next-episode")
async def get_next_episode(user: User = Depends(_get_current_user)) -> dict[str, Any]:
    next_play = service.get_next_episode(user)
    return next_play.model_dump()


@app.get("/user/{name}/previous-episode")
async def get_previous_episode(
    user: User = Depends(_get_current_user),
) -> dict[str, Any]:
    previous_play = service.get_previous_episode(user)
    return previous_play.model_dump()


@app.get("/films")
async def get_films() -> dict[str, Any]:
    films = service.get_films()
    return films.model_dump()


@app.get("/film/{film}")
async def get_film(film: str) -> dict[str, Any]:
    selection = service.get_film(film)
    return selection.model_dump()


@app.get("/shows")
async def get_shows() -> dict[str, Any]:
    shows = service.get_shows()
    return shows.model_dump()


@app.get("/show/{show}/seasons")
async def get_seasons(show: str) -> dict[str, Any]:
    seasons = service.get_seasons(show)
    return seasons.model_dump()


@app.get("/show/{show}/{season}")
async def get_episodes(show: str, season: int) -> dict[str, Any]:
    episodes = service.get_episodes(show, season)
    return episodes.model_dump()


@app.get("/show/{show}/{season}/{episode}")
async def get_episode(show: str, season: int, episode: int) -> dict[str, Any]:
    selection = service.get_episode(show, season, episode)
    return selection.model_dump()


@app.get("/get-paused/{user}")
async def get_paused(user: int) -> dict[str, Any]:
    seconds = service.get_paused_time(user)
    return seconds.model_dump()


@app.post("/record-play")
async def record_play(body: Watched):
    play_time = datetime.now()
    statement = "insert into history (file_key, time, user_id) values (:file_key, :time, :user_id);"
    params = {"file_key": body.file_key, "time": play_time, "user_id": body.user_id}
    execute_statement(statement, params)
    return {"status_code": 200, "detail": f"Recorded play - file key: {body.file_key}"}


@app.post("/record-paused")
async def paused_play(body: PausedPlay):
    statement = (
        "insert into paused_content (user_id, video_progress)"
        "values (:user_id, :video_progress);"
    )
    params = {
        "user_id": body.user_id,
        "video_progress": body.video_progress,
    }
    execute_statement(statement, params)
    return {"status_code": 200, "detail": "Recorded paused"}
