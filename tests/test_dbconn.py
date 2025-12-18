from src import dbconn
from pathlib import Path


def test_gather_content_type():
    foo = dbconn.gather_content()
    assert isinstance(foo, list)


def test_gather_shows_data():
    shows_data = dbconn.gather_shows_data()
    assert isinstance(shows_data, dict)
    assert "images" not in shows_data.keys()
    for x in shows_data.values():
        assert len(x) > 1


def test_gather_films_data():
    films_data = dbconn.gather_films_data()
    assert isinstance(films_data, dict)
    assert "images" not in films_data.keys()
    for x in films_data.values():
        assert len(x) == 1


def test_episode_data():
    season, episode = dbconn.episode_data(
        Path("/media/idr/ExtDrive/Chaplifx2/assets/AlanPartridge/S1E1.mp4")
    )
    assert isinstance(season, int)
    assert isinstance(episode, int)
