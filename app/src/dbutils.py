from typing import Any, Sequence
from dotenv import load_dotenv
from sqlalchemy import Engine, Row, create_engine, text
from os import getenv

load_dotenv()


class MissingEnvironmentError(Exception):
    pass


def _create_engine() -> Engine:
    url = getenv("DATABASE_URL")
    if url:
        return create_engine(str(url))
    raise MissingEnvironmentError("DATABASE_URL is not defined in .env file")


db = _create_engine()


def execute_statement(statement: str, engine: Engine = db) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(text(statement))
        conn.commit()


def execute_query(query: str, engine: Engine = db) -> Sequence[Row[Any]]:
    """Funciton to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(text(query))
        return data.fetchall()
