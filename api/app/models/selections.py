from pydantic import BaseModel


class AutoPlay(BaseModel):
    file: str
    show: str | None
    season: int | None
    episode: int | None
    file_key: int


class LastPlayed(BaseModel):
    media_type: str
    file_key: int
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    file: str
