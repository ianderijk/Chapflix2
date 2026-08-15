from fastapi import FastAPI, HTTPException
from api.app.models.user import User
import api.app.service.service as service


app = FastAPI()


def get_current_user(name: str) -> User:
    user = service.get_user(name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{name}' not found")
    return user
