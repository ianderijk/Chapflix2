from datetime import datetime
from pydantic import BaseModel


class BaseMedia(BaseModel):
    """Core identifiers present in every media item."""

    file: str
    file_key: int


class BaseTrackedMedia(BaseMedia):
    """Media items that track watch statistics."""

    plays: int | None = None
    last_played: datetime | None = None


class BaseEpisodeInfo(BaseModel):
    """Shared fields for TV episode metadata."""

    show: str
    season: int
    episode: int


class AutoPlay(BaseMedia):
    show: str | None = None
    season: int | None = None
    episode: int | None = None


class LastPlayed(BaseMedia):
    media_type: str
    film: str | None = None
    show: str | None = None
    season: int | None = None
    episode: int | None = None


class Film(BaseTrackedMedia):
    name: str


class Episode(BaseTrackedMedia, BaseEpisodeInfo):
    """Uses multiple inheritance to combine media tracking + episode metadata."""
