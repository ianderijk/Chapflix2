from ..src import dbconn


def test_gather_content_type():
    foo = dbconn.gather_content()
    assert isinstance(foo, list)
