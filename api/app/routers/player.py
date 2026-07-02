from fastapi import FastAPI, HTTPException
from typing import Any
import api.app.service.service as service

app = FastAPI()

USERS = ["chap", "lady"]


class InvalidUser(HTTPException):
    status_code = 422
    detail = "Invalid user selection"


def _validate_username(username: str) -> None:
    if username.lower() in USERS:
        return
    raise InvalidUser(422)


@app.get("/user/{username}/last-played")
async def get_last_played(username: Any) -> dict[str, Any]:
    _validate_username(username)
    last_played = service.get_last_played(username)
    return last_played


@app.get("user/{username}/next-episode")
async def get_next_episode(username: Any) -> dict[str, Any]:
    _validate_username(username)
    next_play = service.get_next_episode(username)
    return next_play
