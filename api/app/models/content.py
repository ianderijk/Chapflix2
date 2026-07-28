from pydantic import BaseModel
from datetime import datetime


class Films(BaseModel):
    films: list[str]


class Shows(BaseModel):
    shows: list[str]


class Seasons(BaseModel):
    seasons: list[int]


class Episodes(BaseModel):
    episodes: list[int]


class Film(BaseModel):
    name: str
    file: str
    file_key: int
    plays: int | None
    last_played: datetime | None


class Episode(BaseModel):
    show: str
    season: int
    episode: int
    file: str
    file_key: int
    plays: int | None
    last_played: datetime | None
