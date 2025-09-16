from __future__ import annotations
from pathlib import Path
import os
from sqlalchemy import Engine, text, create_engine
from dotenv import load_dotenv


load_dotenv()


MEDIA_FILES = Path(os.path.join(Path(__file__).parent.parent), "assets")
db = create_engine(str(os.getenv("DATABASE_URL")))


def execute_statement(statement: str, engine: Engine = db) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(text(statement))
        conn.commit()


def execute_query(query: str, engine: Engine = db):
    """Funciton to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(text(query))
        return data.fetchall()


def build_tables() -> None:
    execute_statement("call create_schema_tables()")


def gather_content() -> list:
    """Function to gather the data required for the content table on an
    initial load"""
    folders = os.listdir(MEDIA_FILES)
    contents = []
    for x in folders:
        if x == "images":
            continue
        contents += [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
        ]
    return contents


def write_contents_data() -> None:
    content = gather_content()
    for i, x in enumerate(content):
        execute_statement(f"""INSERT INTO content (file_key, file) VALUES (
                          {i}, '{x}'
                          );""")


def incremental_gather_content() -> list:
    """Function to gather data required to add new content to the content table"""
    folders = os.listdir(MEDIA_FILES)
    existing_content_data = execute_query("select file from content")
    existing_content = [x[0] for x in existing_content_data]
    contents = []
    for x in folders:
        if x == "images":
            continue
        contents += [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
            if os.path.join(MEDIA_FILES, x, y) not in existing_content
        ]
    return contents


def incremental_write_contents_data() -> None:
    file_key_data = execute_query("select max(file_key) from content")
    max_file_key: int = file_key_data[0][0] + 1
    content = incremental_gather_content()
    for i, x in enumerate(content, start=max_file_key):
        execute_statement(f"""INSERT INTO content (file_key, file) VALUES (
                          {i}, '{x}'
                          );""")


def gather_shows_data() -> dict:
    results = {}
    folders = os.listdir(MEDIA_FILES)
    for x in folders:
        if x == "images":
            continue
        contents = [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
        ]
        if len(contents) == 1:  # film folders contain a single file so skip these
            continue
        results[x] = contents
    return results


def gather_films_data() -> dict:
    results = {}
    folders = os.listdir(MEDIA_FILES)
    for x in folders:
        if x == "images":
            continue
        contents = [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
        ]
        if len(contents) > 1:  # show folders contain multiple files so skip these
            continue
        results[x] = contents
    return results


def incremental_gather_shows_data() -> dict:
    folders = os.listdir(MEDIA_FILES)
    missing_content_data = execute_query("select * from incremental_load_content()")
    missing_content = [x[0] for x in missing_content_data]
    results = {}
    for x in folders:
        if x == "images":
            continue
        contents = [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
            if os.path.join(MEDIA_FILES, x, y) in missing_content
        ]
        if len(contents) == 0:
            continue
        elif len(contents) == 1:
            continue
        results[x] = contents
    return results


def incremental_gather_films_data() -> dict:
    folders = os.listdir(MEDIA_FILES)
    missing_content_data = execute_query("select * from incremental_load_content()")
    missing_content = [x[0] for x in missing_content_data]
    results = {}
    for x in folders:
        if x == "images":
            continue
        contents = [
            os.path.join(MEDIA_FILES, x, y)
            for y in os.listdir(os.path.join(MEDIA_FILES, x))
            if os.path.join(MEDIA_FILES, x, y) in missing_content
        ]
        if len(contents) == 0:
            continue
        elif len(contents) > 1:
            continue
        results[x] = contents
    return results


def episode_data(episode_file: Path) -> tuple:
    file = episode_file.stem
    season = int(file[file.index("S") + 1 : file.index("E")])
    episode = int(file[file.index("E") + 1 :])
    return season, episode


def write_films_shows_data(incremental: bool) -> None:
    if incremental:
        shows = incremental_gather_shows_data()
        films = incremental_gather_films_data()
    else:
        shows = gather_shows_data()
        films = gather_films_data()
    for show, episodes in shows.items():
        for file in episodes:
            season, episode = episode_data(Path(file))
            file_data = execute_query(f"select * from content where file = '{file}'")
            file_key = file_data[0][0]
            execute_statement(
                f"""INSERT INTO shows (file_key, show, season, episode) VALUES (
                {file_key}, '{show}', {season}, {episode}
                );"""
            )
    for film, file in films.items():
        file_data = execute_query(f"select * from content where file = '{file[0]}'")
        file_key = file_data[0][0]
        execute_statement(
            f"""INSERT INTO films (file_key, film) VALUES (
            {file_key}, '{film}'
            );"""
        )


def initial_build() -> None:
    build_tables()
    write_contents_data()
    write_films_shows_data(False)


def incremental_build() -> None:
    incremental_write_contents_data()
    write_films_shows_data(True)


if __name__ == "__main__":
    incremental_build()