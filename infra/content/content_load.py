import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import NamedTuple
from contextvars import ContextVar
from utils.dbutils import (
    execute_query,
    execute_statement,
    execute_bulk_insert,
    get_table,
    TABLES,
)
from dotenv import load_dotenv

load_dotenv()


class MalformedContentError(Exception):
    pass


class MissingEnvVarError(Exception):
    pass


class ContentType(Enum):
    SHOW = "show"
    FILM = "film"


class Content(NamedTuple):
    type_: ContentType
    filepath: Path
    loaded: bool


class Episode(NamedTuple):
    show: str
    season: int
    episode: int
    filepath: Path
    duration: float


class Film(NamedTuple):
    film: str
    filepath: Path
    duration: float


class PreparedContents(NamedTuple):
    shows: list[Episode]
    films: list[Film]


def _get_video_length(file_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return float(result.stdout)


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


def _tables_exist() -> bool:
    tables_data = execute_query(
        "select table_name from information_schema.tables where table_schema = 'public';"
    )
    tables = [x[0] for x in tables_data]
    return all(x in tables for x in TABLES)


def _get_loaded_content() -> dict[Path, int] | dict:
    """
    Produces a list of content already ingested

    Returns:
        - records: `["ShowName/S1E2.mp4", "FilmName/FilmName.mp4]`
    """
    if not _tables_exist():
        return {}
    loaded_content_data = execute_query("select file, file_key from public.content;")
    records = {}
    for record in loaded_content_data:
        path = Path(record[0])
        stripped_path = _strip_path(path)
        records[stripped_path] = record[1]
    return records


def _get_media_files() -> Path:
    path = os.getenv("MEDIA_FILES")
    if path:
        return Path(path)

    raise MissingEnvVarError(
        "No env var for media files, please set one in the root .env file"
    )


MEDIA_FILES = _get_media_files()
loaded_content = ContextVar("loaded_content", default={})
is_content_loaded = True if loaded_content.get() else False


def _is_loaded(stripped_path: Path) -> bool:
    _loaded_content = loaded_content.get()
    return stripped_path in _loaded_content


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
    duration = _get_video_length(show.filepath)
    return Episode(show_name, int(season), int(episode), show.filepath, duration)


def _process_film_content(film: Content) -> Film:
    film_name = film.filepath.parent.stem
    duration = _get_video_length(film.filepath)
    return Film(film_name, film.filepath, duration)


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


def load_content(episodes: list[Episode], films: list[Film]) -> None:
    episode_paths = [{"file": str(x.filepath)} for x in episodes]
    film_paths = [{"file": str(x.filepath)} for x in films]
    content_paths = episode_paths + film_paths
    if not content_paths:
        return

    execute_bulk_insert(get_table("content"), content_paths)
    loaded_content.set(_get_loaded_content())


def load_episodes(episodes: list[Episode]) -> None:
    _loaded_content = loaded_content.get()
    shows_table_values = [
        {
            "file_key": _loaded_content[_strip_path(x.filepath)],
            "show": x.show,
            "season": x.season,
            "episode": x.episode,
            "duration": x.duration,
        }
        for x in episodes
    ]
    execute_bulk_insert(get_table("shows"), shows_table_values)


def load_films(films: list[Film]) -> None:
    _loaded_content = loaded_content.get()
    films_table_values = [
        {
            "file_key": _loaded_content[_strip_path(x.filepath)],
            "film": x.film,
            "duration": x.duration,
        }
        for x in films
    ]
    execute_bulk_insert(get_table("films"), films_table_values)


def _build_tables() -> None:
    execute_statement("call create_schema_tables()")


def _build_functions() -> None:
    shell_path = (
        Path(__file__).parent.parent.parent
        / "infra"
        / "postgres"
        / "dbo"
        / "reset_functions.sh"
    )
    subprocess.run(["bash", shell_path], check=True)


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


def manual_inserts() -> None:
    _insert_users()
    _insert_dummy_history_records()


def load_db() -> None:
    initial_load = not _tables_exist()
    if initial_load:
        build_db()
    contents = walk_content(MEDIA_FILES)
    prepared = prepare_contents(contents)
    load_content(prepared.shows, prepared.films)
    if prepared.shows:
        load_episodes(prepared.shows)
    if prepared.films:
        load_films(prepared.films)
    if initial_load:
        manual_inserts()
