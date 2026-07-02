from fastapi import FastAPI, HTTPException
from typing import Any

app = FastAPI()


@app.get("/user/{username}")
async def get_user_id(username: Any) -> dict[str, Any]:
    if username.lower() not in ["chap", "lady"]:
        raise HTTPException(
            status_code=422, detail=f"Invalid user selection: {username}"
        )
    return {"str": None}
