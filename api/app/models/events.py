from pydantic import BaseModel


class Watched(BaseModel):
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    user_id: int
