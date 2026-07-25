import json
from typing import Any
from utils.dbutils import execute_query
from api.app.models.last_played import LastPlayed
from api.app.models.auto_play import AutoPlay
from api.app.middleware.api_logger import logger


def _create_model_dict(model, values: list) -> dict[Any, Any]:
    keys = model.model_fields.keys()
    records = {k: v for k, v in zip(keys, values)}
    return json.loads(model(**records).model_dump_json())


def _get_user_id(username: str) -> int:
    query = "select * from users where display_name = :display_name"
    params = {"display_name": username}
    data = execute_query(query, params)
    logger.debug(f"Data from _get_user_id: {data}")
    return data[0][0]


def get_last_played(username: str) -> dict[str, Any]:
    user_id = _get_user_id(username)
    query = "select * from get_last_played(:user_id)"
    params = {"user_id": user_id}
    data = execute_query(query, params)
    values = list(data[0])
    return _create_model_dict(LastPlayed, values)


def get_next_episode(username: str) -> dict[str, Any]:
    user_id = _get_user_id(username)
    query = "select * from get_next_episode(:user_id)"
    params = {"user_id": user_id}
    data = execute_query(query, params)
    values = list(data[0])
    return _create_model_dict(AutoPlay, values)
