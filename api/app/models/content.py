from pydantic import BaseModel


class Films(BaseModel):
    films: list[str]


class Shows(BaseModel):
    shows: list[str]


class Seasons(BaseModel):
    seasons: list[int]


class Episodes(BaseModel):
    episodes: list[int]
