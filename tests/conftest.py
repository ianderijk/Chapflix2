from unittest.mock import patch

with patch("app.src.dbutils.execute_query", return_value=[]):
    import app.src.content  # noqa: F401
