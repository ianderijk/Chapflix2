from typing import Optional
from pydantic import BaseModel


class LastPlayed(BaseModel):
    media_type: str
    file_key: int
    film: Optional[str]
    show: Optional[str]
    season: Optional[int]
    episode: Optional[int]
    file: str
