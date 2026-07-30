from pydantic import BaseModel


class Watched(BaseModel):
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    user_id: int
    file_key: int


class PausedPlay(BaseModel):
    user_id: int
    video_progress: float


class ResumePaused(BaseModel):
    seconds: float
