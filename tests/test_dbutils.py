from utils.dbutils import (
    execute_statement,
    execute_query,
)
from unittest.mock import MagicMock


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
