from pydantic import BaseModel


class LastPlayed(BaseModel):
    media_type: str
    file_key: int
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    file: str
