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
    content = """
    CREATE TABLE IF NOT EXISTS content (
        file_key INTEGER PRIMARY KEY,
        file TEXT
    )
    """

    films = """
    CREATE TABLE IF NOT EXISTS films (
        file_key INTEGER PRIMARY KEY,
        film TEXT,
        FOREIGN KEY (file_key) REFERENCES content(file_key)
    )
    """

    shows = """
    CREATE TABLE IF NOT EXISTS shows (
        file_key INTEGER PRIMARY KEY,
        show TEXT,
        season INTEGER,
        episode INTEGER,
        FOREIGN KEY (file_key) REFERENCES content(file_key)
    )
    """

    history = """
    CREATE TABLE IF NOT EXISTS history (
        play_num SERIAL PRIMARY KEY,
        file_key INTEGER,
        time TIMESTAMP,
        FOREIGN KEY (file_key) REFERENCES content(file_key)
    )
    """
    execute_statement(content)
    execute_statement(films)
    execute_statement(shows)
    execute_statement(history)


def gather_content() -> list:
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


def episode_data(episode_file: Path) -> tuple:
    file = episode_file.stem
    season = int(file[file.index("S") + 1 : file.index("E")])
    episode = int(file[file.index("E") + 1 :])
    return season, episode


def write_films_shows_data() -> None:
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


def main() -> None:
    """Function to build database on initial setup"""
    build_tables()
    write_contents_data()
    write_films_shows_data()


if __name__ == "__main__":
    print("hello from dbconn!")
