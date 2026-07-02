from typing import Optional
from pydantic import BaseModel


class AutoPlay(BaseModel):
    file: str
    show: Optional[str]
    season: Optional[int]
    episode: Optional[int]
