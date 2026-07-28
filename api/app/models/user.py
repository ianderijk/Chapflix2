from pydantic import BaseModel


class User(BaseModel):
    id_: int
    name: str
