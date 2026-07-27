from pydantic import BaseModel


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


class Episode(BaseModel):
    show: str
    season: int
    episode: int
    file: str
