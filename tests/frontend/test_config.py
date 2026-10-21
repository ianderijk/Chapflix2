import pytest

from app.src import config


@pytest.mark.parametrize(
    "variable", [config.API_URL_VARIABLE, config.MEDIA_FILES_VARIABLE]
)
def test_startup_fails_without_configuration(monkeypatch, variable):
    monkeypatch.delenv(variable)
    with pytest.raises(config.MissingConfigurationError, match=variable):
        config.check()


def test_startup_succeeds_with_configuration():
    config.check()
