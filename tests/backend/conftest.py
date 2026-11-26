from contextvars import ContextVar
import pytest


@pytest.fixture(autouse=True)
def set_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://postgres:password123@192.168.0.72:6543/chapflix")


@pytest.fixture
def media_files(monkeypatch, tmp_path):
    patch = ContextVar("media_files", default=tmp_path)
    monkeypatch.setattr(
        "infra.content.content_load.media_files",
        patch
    )
    return patch


@pytest.fixture
def create_test_files(media_files):
    def create_file_and_dir(path):
        if path.exists():
            return

        if not path.parent.exists():
            path.parent.mkdir()

        path.touch()

    path = media_files.get()
    files = [
        path / "Film" / "Film.mp4",
        path / "Show" / "S1E1.mp4",
        path / "Show" / "S1E2.mp4",
    ]
    for file in files:
        create_file_and_dir(file)
