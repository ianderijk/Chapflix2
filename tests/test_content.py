import pytest
from pathlib import Path
from unittest.mock import patch
import app.src.content as content
from app.src.content import (
    FileKey,
    Content,
    ContentType,
    Episode,
    Film,
    MalformedContentError,
)


def test_strip_path():
    path = content.MEDIA_FILES / "Show/S1E2.mp4"
    stripped_path = content._strip_path(path)
    expected = Path("Show/S1E2.mp4")
    assert stripped_path == expected


def test_file_key_starts_after_existing_max():
    with patch("app.src.content.execute_query", return_value=[(5,)]):
        file_key = FileKey()
    assert file_key() == 6
    assert file_key() == 7


def test_file_key_starts_at_1_on_empty_table():
    with patch("app.src.content.execute_query", return_value=[(None,)]):
        file_key = FileKey()
    assert file_key() == 1
    assert file_key() == 2


def test_is_loaded_returns_true_on_loaded():
    path = Path("/show/S1E2.mp4")
    loaded = [path]
    with patch.object(content, "LOADED_CONTENT", loaded):
        assert content._is_loaded(path)


def test_is_loaded_returns_false_on_non_loaded():
    loaded_path = Path("/show/S1E2.mp4")
    non_loaded_path = Path("/show/S1E3.mp4")
    loaded_content = [loaded_path]
    with patch.object(content, "LOADED_CONTENT", loaded_content):
        assert not content._is_loaded(non_loaded_path)


def test_walk_single_file_dir_is_film(tmp_path):
    film_dir = tmp_path / "Film"
    film_dir.mkdir()
    film_file = film_dir / "Film.mp4"
    film_file.touch()

    with (
        patch.object(content, "LOADED_CONTENT", []),
        patch.object(content, "MEDIA_FILES", tmp_path),
    ):
        results = content.walk_content(tmp_path)

    assert len(results) == 1

    film = results[0]
    assert film.type_ is ContentType.FILM
    assert not film.loaded


def test_walk_multiple_files_dir_is_show(tmp_path):
    show_dir = tmp_path / "Show"
    show_dir.mkdir()
    show_file_one = show_dir / "S1E1.mp4"
    show_file_two = show_dir / "S1E2.mp4"
    show_file_one.touch()
    show_file_two.touch()

    with (
        patch.object(content, "LOADED_CONTENT", []),
        patch.object(content, "MEDIA_FILES", tmp_path),
    ):
        results = content.walk_content(tmp_path)

    assert len(results) == 2
    assert all(x.type_ is ContentType.SHOW for x in results)
    assert all(not x.loaded for x in results)


def test_walk_mixed_dirs(tmp_path):
    show_dir = tmp_path / "Show"
    show_dir.mkdir()
    show_file_one = show_dir / "S1E1.mp4"
    show_file_two = show_dir / "S1E2.mp4"
    show_file_one.touch()
    show_file_two.touch()

    film_dir = tmp_path / "Film"
    film_dir.mkdir()
    film_file = film_dir / "Film.mp4"
    film_file.touch()

    with (
        patch.object(content, "LOADED_CONTENT", []),
        patch.object(content, "MEDIA_FILES", tmp_path),
    ):
        results = content.walk_content(tmp_path)

    assert len(results) == 3

    film = [x for x in results if x.type_ is ContentType.FILM]
    shows = [x for x in results if x.type_ is ContentType.SHOW]

    assert all(x.type_ is ContentType.FILM for x in film)
    assert all(x.type_ is ContentType.SHOW for x in shows)


def _make_show(filename: str, loaded: bool) -> Content:
    filepath = Path("/content/Show") / filename
    return Content(ContentType.SHOW, filepath, loaded)


def test_process_show_content():
    show = _make_show("S1E1.mp4", True)
    processed_show = content._process_show_content(show)

    assert processed_show.show == "Show"
    assert processed_show.season == 1
    assert processed_show.episode == 1
    assert processed_show.filepath == Path("/content/Show/S1E1.mp4")


def test_process_malformed_show_content():
    show = _make_show("invalid_file_name.mp4", True)
    with pytest.raises(MalformedContentError):
        content._process_show_content(show)


def _make_film(filename: str, loaded: bool) -> Content:
    filepath = Path("/content/Film") / filename
    return Content(ContentType.FILM, filepath, loaded)


def test_process_film_content():
    film = _make_film("Film.mp4", True)
    processed_film = content._process_film_content(film)

    assert processed_film.film == "Film"
    assert processed_film.filepath == Path("/content/Film/Film.mp4")


def test_prepare_contents():
    loaded_shows = [_make_show(x, True) for x in ["S1E1.mp4", "S1E2.mp4"]]
    non_loaded_shows = [_make_show(x, False) for x in ["S2E1.mp4", "S2E2.mp4"]]
    loaded_films = [_make_film(x, True) for x in ["Film1.mp4", "Film2.mp4"]]
    non_loaded_films = [_make_film(x, False) for x in ["Film3.mp4", "Film4.mp4"]]

    contents = loaded_shows + non_loaded_shows + loaded_films + non_loaded_films
    prepared_contents = content.prepare_contents(contents)

    prepared_shows = prepared_contents.shows
    prepared_films = prepared_contents.films

    expected_shows = [
        Episode("Show", 2, 1, 3, Path("/content/Show/S2E1.mp4")),
        Episode("Show", 2, 2, 4, Path("/content/Show/S2E2.mp4")),
    ]
    expected_films = [
        Film("Film", 5, Path("/content/Film/Film3.mp4")),
        Film("Film", 6, Path("/content/Film/Film4.mp4")),
    ]
    assert prepared_shows == expected_shows
    assert prepared_films == expected_films
