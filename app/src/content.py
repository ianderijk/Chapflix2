import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import NamedTuple
from app.src.dbutils import (
    execute_query,
    execute_statement,
    execute_bulk_insert,
    TABLES,
)


class MalformedContentError(Exception):
    pass


class ContentType(Enum):
    SHOW = "show"
    FILM = "film"


class FileKey:
    def __init__(self) -> None:
        self.file_key: int = self._set_file_key()

    def _set_file_key(self) -> int:
        file_key_data = execute_query("select max(file_key) file_key from content;")

        # For full load there will be no data in the content table meaning the
        # query will return an empty list
        if file_key_data and file_key_data[0][0]:
            return file_key_data[0][0] + 1

        # If there are no records in the table set file key to be 1
        return 1

    def __call__(self) -> int:
        cur_val = self.file_key
        self.file_key += 1
        return cur_val


Content = NamedTuple(
    "Content", [("type_", ContentType), ("filepath", Path), ("loaded", bool)]
)

Episode = NamedTuple(
    "Episode",
    [
        ("show", str),
        ("season", int),
        ("episode", int),
        ("file_key", int),
        ("filepath", Path),
    ],
)

Film = NamedTuple("Film", [("film", str), ("file_key", int), ("filepath", Path)])

PreparedContents = NamedTuple(
    "PreparedContents", [("shows", list[Episode]), ("films", list[Film])]
)


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


def _get_loaded_content() -> list[Path]:
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
LOADED_CONTENT = _get_loaded_content()
FILE_KEY = FileKey()


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


def _get_file_key_mappings() -> dict[Path, int]:
    content_data = execute_query("select * from content;")
    return {Path(x[1]): int(x[0]) for x in content_data}


FILE_KEY_MAPPINGS = _get_file_key_mappings()


def _process_show_content(show: Content) -> Episode:
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
    if file_key is None:
        return Episode(show_name, int(season), int(episode), FILE_KEY(), show.filepath)
    return Episode(show_name, int(season), int(episode), file_key, show.filepath)


def _process_film_content(film: Content) -> Film:
    film_name = film.filepath.parent.stem
    file_key = FILE_KEY_MAPPINGS.get(film.filepath)
    if file_key is None:
        return Film(film_name, FILE_KEY(), film.filepath)
    return Film(film_name, file_key, film.filepath)


def prepare_contents(
    contents: list[Content],
) -> PreparedContents:
    films = []
    shows = []
    for content in contents:
        if content.loaded:
            continue

        if content.type_ is ContentType.SHOW:
            episode = _process_show_content(content)
            shows.append(episode)
        elif content.type_ is ContentType.FILM:
            film = _process_film_content(content)
            films.append(film)
        else:
            raise MalformedContentError(f"{content} is not of type show or film")

    return PreparedContents(shows, films)


def load_episodes(episodes: list[Episode]) -> None:
    content_table_values = [
        {"file_key": x.file_key, "file": x.filepath} for x in episodes
    ]
    shows_table_values = [
        {
            "file_key": x.file_key,
            "show": x.show,
            "season": x.season,
            "episode": x.episode,
        }
        for x in episodes
    ]
    execute_bulk_insert("content", content_table_values)
    execute_bulk_insert("shows", shows_table_values)


def load_films(films: list[Film]) -> None:
    content_table_values = [{"file_key": x.file_key, "file": x.filepath} for x in films]
    films_table_values = [{"file_key": x.file_key, "film": x.film} for x in films]
    execute_bulk_insert("content", content_table_values)
    execute_bulk_insert("films", films_table_values)


def _tables_exist() -> bool:
    tables_data = execute_query(
        "select table_name from information_schema.tables; where table_schema = 'public'"
    )
    tables = [x[0] for x in tables_data]
    return all(x in tables for x in TABLES.keys())


def _build_tables() -> None:
    execute_statement("call create_schema_tables()")


def _build_functions() -> None:
    shell_path = (
        Path(__file__).parent.parent.parent
        / "infra"
        / "postgres"
        / "reset_functions.sh"
    )
    subprocess.run(["bash", shell_path])


def _insert_users() -> None:
    execute_statement("insert into users (display_name) values ('Lady'), ('Chap');")


def _insert_dummy_history_records() -> None:
    execute_statement(
        f"insert into history (file_key, time, user_id) values (1, '{datetime.now()}', 1)"
    )
    execute_statement(
        f"insert into history (file_key, time, user_id) values (1, '{datetime.now()}', 2)"
    )


def build_db() -> None:
    _build_tables()
    _build_functions()
    _insert_users()
    _insert_dummy_history_records()


def load_db() -> None:
    if not _tables_exist():
        build_db()
    contents = walk_content(MEDIA_FILES)
    prepared = prepare_contents(contents)
    if prepared.shows:
        load_episodes(prepared.shows)
    if prepared.films:
        load_films(prepared.films)
