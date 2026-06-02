from app.src.dbconn import (
    execute_statement,
    execute_query,
    gather_content,
    gather_shows_data,
    gather_films_data,
    episode_data,
    incremental_gather_content,
)
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_execute_statement():
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    execute_statement("create table test;", engine=mock_engine)
    mock_engine.connect.assert_called_once()
    mock_conn.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_execute_query():
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.execute.return_value.fetchall.return_value = [("row1"), ("row2")]
    result = execute_query("select * from test;", engine=mock_engine)
    mock_engine.connect.assert_called_once()
    mock_conn.execute.assert_called_once()
    assert result == [("row1"), ("row2")]


def test_gather_content():
    foo = gather_content()
    assert isinstance(foo, list)
    assert all(isinstance(x, Path) for x in foo)


def test_gather_shows_data():
    shows_data = gather_shows_data()
    assert isinstance(shows_data, dict)
    assert "images" not in shows_data.keys()
    for x in shows_data.values():
        assert len(x) > 1


def test_gather_films_data():
    films_data = gather_films_data()
    assert isinstance(films_data, dict)
    assert "images" not in films_data.keys()
    for x in films_data.values():
        assert len(x) == 1


def test_episode_data():
    season, episode = episode_data(
        Path("/media/idr/ExtDrive/Chaplifx2/content/AlanPartridge/S1E1.mp4")
    )
    assert isinstance(season, int)
    assert isinstance(episode, int)
    assert season == 1
    assert episode == 1


@patch("app.src.dbconn.execute_query")
@patch("app.src.dbconn.MEDIA_FILES", Path("test/content"))
@patch("app.src.dbconn.os.listdir")
def test_incremental_gather_content(mock_listdir, mock_execute_query):
    mock_listdir.side_effect = [
        ["show1", "show2"],
        ["file1.mp4"],
        ["file2.mp4"],
    ]

    mock_execute_query.return_value = [("test/content/show1/file1.mp4",)]
    result = incremental_gather_content()
    expected_result = [Path("test/content/show2/file2.mp4")]
    assert result == expected_result
