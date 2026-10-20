from typing import Any, Sequence, Mapping
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Engine, Row, create_engine, text, insert
from contextvars import ContextVar
import os

load_dotenv()


class MissingEnvironmentError(Exception):
    pass


metadata = MetaData(schema="public")
engine: Any = ContextVar("engine", default=None)


def _create_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if url:
        return create_engine(str(url))
    raise MissingEnvironmentError("DATABASE_URL is not defined in .env file")


def get_engine() -> Engine:
    if engine.get() is None:
        engine.set(_create_engine())
    return engine.get()


TABLES = {"content", "films", "history", "paused_content", "shows", "users"}


def get_table(table_name: str) -> Table:
    if table_name not in TABLES:
        raise KeyError(
            f"Invalid table name '{table_name}'. Select from: {', '.join(TABLES)}"
        )
    return Table(table_name, metadata, autoload_with=get_engine())


def execute_statement(
    statement: str, params: Mapping[str, Any] = {}, engine: Engine | None = None
) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    if engine is None:
        engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(statement), params)
        conn.commit()


def execute_query(
    query: str, params: Mapping[str, Any] = {}, engine: Engine | None = None
) -> Sequence[Row[Any]]:
    """Funciton to allow execution of queries that return results"""
    if engine is None:
        engine = get_engine()
    with engine.connect() as conn:
        data = conn.execute(text(query), params)
        return data.fetchall()


def execute_bulk_insert(
    table: Table, values: list[dict[str, Any]], engine: Engine | None = None
) -> None:
    if engine is None:
        engine = get_engine()
    with engine.begin() as conn:
        conn.execute(insert(table), values)
