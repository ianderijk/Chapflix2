from typing import Any, Sequence
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, Engine, Row, create_engine, text, insert
from os import getenv

load_dotenv()


class MissingEnvironmentError(Exception):
    pass


metadata = MetaData(schema="public")


def _create_engine() -> Engine:
    url = getenv("DATABASE_URL")
    if url:
        return create_engine(str(url))
    raise MissingEnvironmentError("DATABASE_URL is not defined in .env file")


engine = _create_engine()

TABLES = {
    "content": Table("content", metadata, autoload_with=engine),
    "films": Table("films", metadata, autoload_with=engine),
    "history": Table("history", metadata, autoload_with=engine),
    "paused_content": Table("paused_content", metadata, autoload_with=engine),
    "shows": Table("shows", metadata, autoload_with=engine),
    "users": Table("users", metadata, autoload_with=engine),
}


def execute_statement(statement: str, engine: Engine = engine) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(text(statement))
        conn.commit()


def execute_query(query: str, engine: Engine = engine) -> Sequence[Row[Any]]:
    """Funciton to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(text(query))
        return data.fetchall()


def execute_bulk_insert(
    table_name: str, values: list[dict[str, Any]], engine: Engine = engine
) -> None:
    table = TABLES[table_name]
    with engine.begin() as conn:
        conn.execute(insert(table), values)
