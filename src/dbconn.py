from __future__ import annotations
from pathlib import Path
import os
import sqlalchemy as sa


MEDIA_FILES = Path(os.path.join(Path(__file__).parent.parent), "assets")
DB_ADDRESS = Path(os.path.join(Path(__file__).parent.parent, "Chapflix.db"))
db = sa.create_engine(f"sqlite:///{DB_ADDRESS}")


def execute_statement(statement: str, engine=db, params: None | dict = None) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(sa.text(statement), params or {})
        conn.commit()


def execute_query(query: str, engine=db):
    """Funciton to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(sa.text(query))
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
        play_num INTEGER PRIMARY KEY AUTOINCREMENT,
        file_key INTEGER,
        time DATETIME,
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
        execute_statement(
            "INSERT INTO content VALUES (:file_key, :file)",
            params={"file_key": i, "file": x},
        )


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
                "INSERT INTO shows VALUES (:file_key, :show, :season, :episode)",
                params={
                    "file_key": file_key,
                    "show": show,
                    "season": season,
                    "episode": episode,
                },
            )
    for film, file in films.items():
        file_data = execute_query(f"select * from content where file = '{file[0]}'")
        file_key = file_data[0][0]
        execute_statement(
            "INSERT INTO films VALUES (:file_key, :film)",
            params={"file_key": file_key, "film": film},
        )


if __name__ == "__main__":
    print("hello from dbconn.py")
