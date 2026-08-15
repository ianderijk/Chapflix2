from typing import Any, Sequence, Mapping
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Engine, Row, create_engine, text, insert
import os

load_dotenv()


class MissingEnvironmentError(Exception):
    pass


metadata = MetaData(schema="public")

_engine = None


def _create_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if url:
        return create_engine(str(url))
    raise MissingEnvironmentError("DATABASE_URL is not defined in .env file")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


TABLES = {
    "content": Table("content", metadata, autoload_with=get_engine()),
    "films": Table("films", metadata, autoload_with=get_engine()),
    "history": Table("history", metadata, autoload_with=get_engine()),
    "paused_content": Table("paused_content", metadata, autoload_with=get_engine()),
    "shows": Table("shows", metadata, autoload_with=get_engine()),
    "users": Table("users", metadata, autoload_with=get_engine()),
}


def execute_statement(
    statement: str, params: Mapping[str, Any] = {}, engine: Engine = get_engine()
) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(text(statement), params)
        conn.commit()


def execute_query(
    query: str, params: Mapping[str, Any] = {}, engine: Engine = get_engine()
) -> Sequence[Row[Any]]:
    """Function to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(text(query), params)
        return data.fetchall()


def execute_bulk_insert(
    table_name: str, values: list[dict[str, Any]], engine: Engine = get_engine()
) -> None:
    table = TABLES[table_name]
    with engine.begin() as conn:
        conn.execute(insert(table), values)
