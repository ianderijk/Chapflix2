import pytest
import os
from pathlib import Path

from infra.content.content_load import _strip_path, walk_content, Content, ContentType


def test_strip_path(media_files):
    path = media_files.get() / "Show" / "S1E3.mp4"
    actual = _strip_path(path)
    expected = Path("Show/S1E3.mp4")
    assert actual == expected


def test_walk_content(media_files, create_test_files):
    expected = [
        Content(ContentType.FILM, media_files.get() / "Film" / "Film.mp4", False),
        Content(ContentType.SHOW, media_files.get() / "Show" / "S1E1.mp4", False),
        Content(ContentType.SHOW, media_files.get() / "Show" / "S1E2.mp4", False),
    ]
    actual = walk_content()

    assert all(x in expected for x in actual)
    assert all(x in actual for x in expected)
