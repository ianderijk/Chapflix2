from pydantic import BaseModel


class Watched(BaseModel):
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    user_id: int
    file_key: int


class Paused(BaseModel):
    play_num: int
    user_id: int
    video_progress: float
