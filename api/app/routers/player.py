from fastapi import FastAPI, Depends, HTTPException
from typing import Any
from api.app.models.user import User
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


@app.get("/{show}/seasons")
async def get_seasons(show: str) -> dict[str, Any]:
    seasons = service.get_seasons(show)
    return seasons.model_dump()


@app.get("/{show}/{season}")
async def get_episodes(show: str, season: int) -> dict[str, Any]:
    episodes = service.get_episodes(show, season)
    return episodes.model_dump()


@app.get("/{show}/{season}/{episode}")
async def get_episode(show: str, season: int, episode: int) -> dict[str, Any]:
    selection = service.get_episode(show, season, episode)
    return selection.model_dump()


# @app.post("/record-play")
# async def record_play(body: Watched):
#     ######################################################################
#     # This endpoint isn't written yet. Any time this endpoint will get called
#     # I need to figure out which endpoints will have provided the data that's
#     # being sent to this endpoint. That get endpoint payload will have to include
#     # the file key. I've updated the get_next_episode function so that now
#     # returns the file key (update made in the database). Just need to figure
#     # out what other sql functions will need updating and do them before
#     # this endpoint can be implemented properly.
#     ######################################################################
#     play_time = datetime.now()
#     value_to_insert = body.value
#     statement = "insert into users (user_id, display_name) values (:id_, 'test')"
#     params = {"id_": value_to_insert}
#     try:
#         execute_statement(statement, params)
#     except Exception:
#         return {"status_code": 500, "detail": "Failed to insert into database"}
#     return {"status_code": 200, "detail": f"inserted {value_to_insert}"}
