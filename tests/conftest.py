import pytest  # noqa: F401
import importlib
import os
import time
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer
from datetime import datetime

DB_FILE_PATH_RECORDS_ROOT = Path("/media/ianderijk/Backup/Chapflix2/content")
REPO_ROOT = Path(__file__).resolve().parents[1]


with patch("app.src.dbutils.execute_query", return_value=[]):
    import app.src.content  # noqa: F401


def _read_sql_file(path: Path) -> str:
    return path.read_text()


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        url = postgres.get_connection_url()
        time.sleep(1)
        yield url


@pytest.fixture(scope="session")
def setup_test_db(postgres_container):
    url = postgres_container
    engine = create_engine(url)

    create_schema_proc = _read_sql_file(
        REPO_ROOT / "infra" / "postgres" / "dbo" / "create_schema_proc.sql"
    )
    with engine.connect() as conn:
        conn.execute(text(create_schema_proc))
        conn.commit()

        conn.execute(text("CALL create_schema_tables();"))
        conn.commit()

        # Essential to maintain ordering here due to interdependencies within functions
        functions_dir = REPO_ROOT / "infra" / "postgres" / "dbo" / "functions"
        function_files = [
            functions_dir / "get_film_path.sql",
            functions_dir / "get_show_path.sql",
            functions_dir / "get_show.sql",
            functions_dir / "incremental_load.sql",
            functions_dir / "get_last_played.sql",
            functions_dir / "get_next_episode.sql",
            functions_dir / "get_previous_episode.sql",
        ]

        for file in function_files:
            function = _read_sql_file(file)
            conn.execute(text(function))
            conn.commit()

        content_dir = DB_FILE_PATH_RECORDS_ROOT / "content"

        show_file1 = str(content_dir / "TestShow" / "S1E1.mp4")
        show_file2 = str(content_dir / "TestShow" / "S1E2.mp4")
        film_file = str(content_dir / "TestFilm" / "Film.mp4")  # Fixed typo

        conn.execute(
            text(
                """INSERT INTO content (file_key, file) VALUES
                (1, :f1), (2, :f2), (3, :f3)
                """
            ),
            {"f1": show_file1, "f2": show_file2, "f3": film_file},
        )
        conn.commit()

        conn.execute(
            text("INSERT INTO films (file_key, film) VALUES (3, :f1)"),
            {"f1": "TestFilm"},  # Just the film name, not the path
        )
        conn.commit()

        conn.execute(
            text(
                """
                INSERT INTO shows (file_key, show, season, episode) VALUES
                (1, 'TestShow', 1, 1), (2, 'TestShow', 1, 2)
                """
            ),
        )
        conn.commit()

        conn.execute(text("INSERT INTO users (display_name) VALUES ('Test')"))
        conn.commit()

        conn.execute(
            text("""
                INSERT INTO history (file_key, time, user_id) VALUES
                (1, :dt, 1)
                """),
            {"dt": datetime.now()},
        )
        conn.commit()

    os.environ["DATABASE_URL"] = url

    import app.src.dbutils as dbutils

    importlib.reload(dbutils)
    import app.src.content as content

    importlib.reload(content)
    import app.src.player as player

    importlib.reload(player)

    yield {"url": url, "engine": engine}
