"""End-to-end playback checks in a real browser against a running app and dev API.

Run with:
    CHAPFLIX_E2E_APP_URL=http://127.0.0.1:8050 \\
    CHAPFLIX_E2E_API_URL=http://localhost:8043 \\
    uv run pytest tests/frontend/test_e2e_playback.py

These tests record plays and pauses for the Chap profile, so only point them at
a dev database. Playwright's Firefox can't keep decoding H.264 after a seek, so
the video's position is faked and media events are dispatched on the real video
element; everything from the app's event listener onwards runs for real.
"""

import os
import time

import pytest
import requests

sync_api = pytest.importorskip("playwright.sync_api")

APP_URL = os.environ.get("CHAPFLIX_E2E_APP_URL")
API_URL = os.environ.get("CHAPFLIX_E2E_API_URL")
pytestmark = pytest.mark.skipif(
    not (APP_URL and API_URL), reason="needs a running app and dev API"
)

FAKE_CLOCK = (
    "const v = document.querySelector('#Player');"
    "if (!v.__fakeClock) { v.__fakeClock = true;"
    " Object.defineProperty(v, 'currentTime', {configurable: true,"
    " get: () => window.__position, set: (t) => { window.__position = t; }}); }"
)
SETTLE_SECONDS = 1.5


def _api(path: str) -> dict:
    return requests.get(f"{API_URL}/{path}", timeout=5).json()


def _emit(page, event: str, position: float) -> None:
    page.evaluate(
        f"{FAKE_CLOCK} window.__position = {position};"
        f" v.dispatchEvent(new Event('{event}'))"
    )
    time.sleep(SETTLE_SECONDS)


def _seconds_before_end(page, seconds: float) -> None:
    duration = _api("user/Chap/last-played")["duration"]
    _emit(page, "timeupdate", duration - seconds)


def _up_next_visible(page) -> bool:
    return "up-next--visible" in (page.locator("#UpNext").get_attribute("class") or "")


def _now_playing(page) -> str:
    return page.locator("#NowPlayingSubtitle").inner_text()


def _wait_for_change(page, previous: str) -> str:
    page.wait_for_function(
        "previous => document.querySelector('#NowPlayingSubtitle').innerText"
        " !== previous",
        arg=previous,
        timeout=15000,
    )
    return _now_playing(page)


def _resume(page) -> str:
    page.locator("#HeroResume").click()
    page.locator("#Theatre:not(.theatre--idle)").wait_for(timeout=15000)
    time.sleep(SETTLE_SECONDS)
    return _now_playing(page)


def _component(type_: str, index: str | int) -> str:
    """Selector for a pattern-matching component, whose DOM id is its JSON id."""
    index_json = f'"{index}"' if isinstance(index, str) else index
    return f"""[id='{{"index":{index_json},"type":"{type_}"}}']"""


def _start_watching_an_episode(page) -> None:
    page.locator(_component("show-card", "TheSimpsons")).click()
    page.locator(_component("episode-tile", 3)).click()
    page.locator("#Theatre:not(.theatre--idle)").wait_for(timeout=15000)


@pytest.fixture(scope="module")
def page():
    with sync_api.sync_playwright() as playwright:
        browser = playwright.firefox.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(APP_URL)
        page.get_by_role("button", name="C Chap").click()
        page.locator("#HeroResume.btn--blood").wait_for(timeout=15000)
        _start_watching_an_episode(page)
        yield page
        browser.close()


def test_pause_is_recorded_and_resumed_for_that_file(page):
    _resume(page)
    _emit(page, "pause", 42)
    file_key = _api("user/Chap/last-played")["file_key"]
    assert _api(f"get-paused/2/{file_key}")["seconds"] == pytest.approx(42)
    page.reload()
    page.locator("#HeroResume.btn--blood").wait_for(timeout=15000)
    assert page.locator("#HeroMeta").inner_text().endswith("Paused at 0:42")
    page.locator("#HeroResume").click()
    page.wait_for_function(
        "(document.querySelector('#Player').getAttribute('src') || '').includes('#t=42')",
        timeout=15000,
    )


def test_countdown_runs_through_the_last_ten_seconds(page):
    _resume(page)
    _seconds_before_end(page, 14)
    assert not _up_next_visible(page)
    _seconds_before_end(page, 8)
    assert _up_next_visible(page)
    assert page.locator("#UpNextCount").inner_text() == "Starting in 8…"
    _seconds_before_end(page, 30)
    assert not _up_next_visible(page)


def test_stay_here_lets_the_episode_finish(page):
    playing = _resume(page)
    _seconds_before_end(page, 6)
    page.locator("#UpNextCancel").click()
    time.sleep(SETTLE_SECONDS)
    assert not _up_next_visible(page)
    _emit(page, "ended", 0)
    assert _now_playing(page) == playing


def test_next_episode_plays_when_the_episode_ends(page):
    playing = _resume(page)
    _seconds_before_end(page, 5)
    _emit(page, "ended", 0)
    assert _wait_for_change(page, playing) != playing
    assert not _up_next_visible(page)


def test_play_now_skips_the_countdown(page):
    playing = _resume(page)
    _seconds_before_end(page, 7)
    page.locator("#UpNextPlay").click()
    assert _wait_for_change(page, playing) != playing


def _final_episode(show: str) -> tuple[int, int]:
    season = _api(f"show/{show}/seasons")["seasons"][-1]
    return season, _api(f"show/{show}/{season}")["episodes"][-1]


def test_no_next_episode_after_the_end_of_a_show(page):
    season, episode = _final_episode("TheThickOfIt")
    page.locator(_component("show-card", "TheThickOfIt")).click()
    page.locator(".show-panel__title", has_text="The Thick Of It").wait_for()
    page.locator(_component("season-tab", season)).click()
    page.locator(".season-tab--active", has_text=f"Season {season}").wait_for()
    page.locator(_component("episode-tile", episode)).click()
    page.wait_for_function(
        "text => document.querySelector('#NowPlayingSubtitle').innerText === text",
        arg=f"Season {season} · Episode {episode}",
        timeout=15000,
    )
    assert _api("user/Chap/next-episode") is None
    page.locator("#HeroNext.btn--hidden").wait_for(state="attached", timeout=15000)
    _seconds_before_end(page, 5)
    assert not _up_next_visible(page)
    assert page.locator("#Notice").inner_text() == ""
