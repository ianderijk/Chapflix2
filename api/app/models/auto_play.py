from pydantic import BaseModel


class AutoPlay(BaseModel):
    file: str
    show: str | None
    season: int | None
    episode: int | None
