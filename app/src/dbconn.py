import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
from typing import NamedTuple
from app.src.dbutils import execute_query, execute_statement

load_dotenv()


class MalformedContentError(Exception):
    pass


class ContentType(Enum):
    SHOW = "show"
    FILM = "film"


Content = NamedTuple(
    "Content", [("type_", ContentType), ("filepath", Path), ("loaded", bool)]
)

Episode = NamedTuple(
    "Episode", [("show", str), ("season", int), ("episode", int), ("file_key", int)]
)

Film = NamedTuple("Film", [("film", str), ("file_key", int)])


def _strip_path(path: Path) -> Path:
    """
    Converts an absolute content path to relative to content parent dir

    Returns:
        - stripped_path

    Example:
        ```
        path = Path("/media/idr/ExtDrive/Chapflix2/content/Show/S1E2.mp4")
        _strip_path(path)
        >>>> Path("Show/S1E2.mp4")
        ```
    """
    return path.relative_to(MEDIA_FILES)


def get_loaded_content() -> list[Path]:
    """
    Produces a list of content already ingested

    Returns:
        - records: `["ShowName/S1E2.mp4", "FilmName/FilmName.mp4]`
    """
    loaded_content_data = execute_query("select file from content;")
    records = []
    for record in loaded_content_data:
        path = Path(record[0])
        stripped_path = _strip_path(path)
        records.append(stripped_path)
    return records


MEDIA_FILES = (Path(__file__).parent.parent.parent) / "content"
LOADED_CONTENT = get_loaded_content()


def _is_loaded(stripped_path: Path) -> bool:
    return stripped_path in LOADED_CONTENT


def walk_content(media_files: Path) -> list[Content]:
    """
    Walks the content directory creating a content record for each file.

    Returns:
        - contents: `[Content(type_: ContentType.SHOW, filepath: Path("path/to/file"), loaded: True]`
    """
    contents = []
    for path, _, files in os.walk(media_files):
        path = Path(path)

        # Skip images directory
        if path.stem == "images":
            continue

        # Films always have a single file
        if len(files) == 1:
            path = path / files[0]
            stripped_path = _strip_path(path)
            loaded = _is_loaded(stripped_path)
            content = Content(ContentType.FILM, path, loaded)
            contents.append(content)
            continue

        # Remaining entries must be shows
        for file in files:
            filepath = path / file
            stripped_path = _strip_path(filepath)
            loaded = _is_loaded(stripped_path)
            content = Content(ContentType.SHOW, filepath, loaded)
            contents.append(content)

    return contents


def build_tables() -> None:
    execute_statement("call create_schema_tables()")


def insert_users() -> None:
    execute_statement("insert into users (display_name) values ('Lady'), ('Chap');")


def insert_dummy_history_records() -> None:
    execute_statement(
        f"insert into history (file_key, time, user_id) values (1, '{datetime.now()}', 1)"
    )
    execute_statement(
        f"insert into history (file_key, time, user_id) values (1, '{datetime.now()}', 2)"
    )


def _get_file_key_mappings() -> dict[Path, int]:
    content_data = execute_query("select * from content;")
    return {Path(x[1]): int(x[0]) for x in content_data}


FILE_KEY_MAPPINGS = _get_file_key_mappings()


def process_show_content(show: Content) -> Episode:
    show_name = show.filepath.parent.stem
    season_episode = show.filepath.stem
    match_ = re.match(r"S(\d+)E(\d+)", season_episode)
    if match_:
        groups = match_.groups()
        season, episode = groups
    else:
        raise MalformedContentError(
            f"{show.filepath} contains invalid filename for episodes"
        )

    file_key = FILE_KEY_MAPPINGS.get(show.filepath)
    if file_key is not None and show.loaded:
        return Episode(show_name, int(season), int(episode), file_key)
    elif file_key and not show.loaded:
        raise MalformedContentError(
            f"{show.filepath} has a file key but is recorded as not loaded"
        )
    raise MalformedContentError(
        f"{show.filepath} recored as loaded but doesn't have a file key"
    )


def process_film_content(film: Content) -> Film:
    film_name = film.filepath.parent.stem
    file_key = FILE_KEY_MAPPINGS.get(film.filepath)
    if file_key is not None and film.loaded:
        return Film(film_name, file_key)
    elif file_key and not film.loaded:
        raise MalformedContentError(
            f"{film.filepath} has a file key but is recorded as not loaded"
        )
    raise MalformedContentError(
        f"{film.filepath} recored as loaded but doesn't have a file key"
    )


# TODO:
# Preparatory steps have now been refactored so that film and episode objects
# are created as required. Next step will be to generate the structures containing
# the records to be inserted into the database and rewrite the insert functions
# to use a batch insert rather than one row at a time. This module also needs
# changing from dbconn to something more apt because this module is now solely
# concerned with loading content while dbutils is the new home of query functions.
# This module can therefore be moved into infra/content_migration.
# It would be nice to re-implement the content table to use a sequential column
# as the file_key column so that this code doesn't have to keep track of inserting
# those.


# def gather_content() -> list[Path]:
#     """Function to gather the data required for the content table on an
#     initial load"""
#     folders = os.listdir(MEDIA_FILES)
#     contents = []
#     for x in folders:
#         if x == "images":
#             continue
#         contents += [MEDIA_FILES / x / y for y in os.listdir(MEDIA_FILES / x)]
#     return contents


# def write_contents_data() -> None:
#     content = gather_content()
#     for i, x in enumerate(content):
#         execute_statement(f"""INSERT INTO content (file_key, file) VALUES (
#                           {i}, '{x}'
#                           );""")


# def incremental_gather_content() -> list[Path]:
#     """Function to gather data required to add new content to the content table"""
#     folders = os.listdir(MEDIA_FILES)
#     existing_content_data = execute_query("select file from content")
#     existing_content = [Path(x[0]) for x in existing_content_data]
#     contents = []
#     for x in folders:
#         if x == "images":
#             continue
#         contents += [
#             MEDIA_FILES / x / y
#             for y in os.listdir(MEDIA_FILES / x)
#             if MEDIA_FILES / x / y not in existing_content
#         ]
#     return contents


# def incremental_write_contents_data() -> None:
#     file_key_data = execute_query("select max(file_key) from content")
#     max_file_key: int = file_key_data[0][0] + 1
#     content = incremental_gather_content()
#     for i, x in enumerate(content, start=max_file_key):
#         execute_statement(f"""INSERT INTO content (file_key, file) VALUES (
#                           {i}, '{x}'
#                           );""")


# def gather_shows_data() -> dict[str, list[Path]]:
#     results = {}
#     folders = os.listdir(MEDIA_FILES)
#     for x in folders:
#         if x == "images":
#             continue
#         contents = [MEDIA_FILES / x / y for y in os.listdir(MEDIA_FILES / x)]
#         if len(contents) == 1:  # film folders contain a single file so skip these
#             continue
#         results[x] = contents
#     return results


# def gather_films_data() -> dict[str, list[Path]]:
#     results = {}
#     folders = os.listdir(MEDIA_FILES)
#     for x in folders:
#         if x == "images":
#             continue
#         contents = [MEDIA_FILES / x / y for y in os.listdir(MEDIA_FILES / x)]
#         if len(contents) > 1:  # show folders contain multiple files so skip these
#             continue
#         results[x] = contents
#     return results


# def incremental_gather_shows_data() -> dict[str, list[Path]]:
#     folders = os.listdir(MEDIA_FILES)
#     missing_content_data = execute_query("select * from incremental_load_content()")
#     missing_content = [x[0] for x in missing_content_data]
#     results = {}
#     for x in folders:
#         if x == "images":
#             continue
#         contents = [
#             MEDIA_FILES / x / y
#             for y in os.listdir(MEDIA_FILES / x)
#             if MEDIA_FILES / x / y in missing_content
#         ]
#         if len(contents) < 2:
#             continue
#         results[x] = contents
#     return results


# def incremental_gather_films_data() -> dict[str, list[Path]]:
#     folders = os.listdir(MEDIA_FILES)
#     missing_content_data = execute_query("select * from incremental_load_content()")
#     missing_content = [x[0] for x in missing_content_data]
#     results = {}
#     for x in folders:
#         if x == "images":
#             continue
#         contents = [
#             MEDIA_FILES / x / y
#             for y in os.listdir(MEDIA_FILES / x)
#             if MEDIA_FILES / x / y in missing_content
#         ]
#         if len(contents) == 0 or len(contents) > 1:
#             continue
#         results[x] = contents
#     return results


# def episode_data(episode_file: Path) -> tuple[int, int]:
#     file = episode_file.stem
#     season = int(file[file.index("S") + 1 : file.index("E")])
#     episode = int(file[file.index("E") + 1 :])
#     return season, episode


# def write_films_shows_data(incremental: bool) -> None:
#     if incremental:
#         shows = incremental_gather_shows_data()
#         films = incremental_gather_films_data()
#     else:
#         shows = gather_shows_data()
#         films = gather_films_data()
#     for show, episodes in shows.items():
#         for file in episodes:
#             season, episode = episode_data(Path(file))
#             file_data = execute_query(f"select * from content where file = '{file}'")
#             show_file_key: int = file_data[0][0]
#             execute_statement(
#                 f"""INSERT INTO shows (file_key, show, season, episode) VALUES (
#                 {show_file_key}, '{show}', {season}, {episode}
#                 );"""
#             )
#     for film, file in films.items():
#         file_data = execute_query(f"select * from content where file = '{file[0]}'")
#         film_file_key: int = file_data[0][0]
#         execute_statement(
#             f"""INSERT INTO films (file_key, film) VALUES (
#             {film_file_key}, '{film}'
#             );"""
#         )


def build_functions() -> None:
    shell_path = (
        Path(__file__).parent.parent.parent
        / "infra"
        / "postgres"
        / "reset_functions.sh"
    )
    subprocess.run(["bash", shell_path])


# def initial_build() -> None:
#     build_tables()
#     insert_users()
#     write_contents_data()
#     write_films_shows_data(False)
#     insert_dummy_history_records()
#     build_functions()


# def incremental_build() -> None:
#     incremental_write_contents_data()
#     write_films_shows_data(True)
