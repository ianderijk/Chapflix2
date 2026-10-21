# Chapflix frontend

A Dash app that talks to the Chapflix API and streams media from `content/`.

## Configuration

Both variables are required and have no defaults, so the app can never talk to
the wrong environment by accident. It refuses to start if either is missing.

| Variable               | Purpose                                                                    |
| ---------------------- | -------------------------------------------------------------------------- |
| `CHAPFLIX_API_URL`     | Base URL of the API                                                        |
| `CHAPFLIX_MEDIA_FILES` | Prefix stripped from the API's `file` paths to get a URL under `/content/` |

`CHAPFLIX_MEDIA_FILES` must match the paths the API returns, which are paths on
the machine that loaded the database, not paths inside the app container. The
container only needs the media mounted at `/app/content`.

## Running locally

```bash
CHAPFLIX_API_URL=http://localhost:8043/ \
CHAPFLIX_MEDIA_FILES=/media/idr/ExtDrive/Chapflix2/ \
uv run -m app.main
```

## Running in a container

On the same Docker network as the API, use the API container's name:

```yaml
environment:
  CHAPFLIX_API_URL: http://chapflix2-api-container:8043/
  CHAPFLIX_MEDIA_FILES: /media/idr/ExtDrive/Chapflix2/
volumes:
  - /media/idr/ExtDrive/Chapflix2/content:/app/content
```

## Layout

| Path                  | What lives there                                                |
| --------------------- | --------------------------------------------------------------- |
| `main.py`             | Creates the Dash app, serves `/content/`, registers callbacks   |
| `src/config.py`       | Required environment variables                                  |
| `src/api_client.py`   | Every call to the API; failures raise `ApiError`                |
| `src/layout.py`       | Component IDs and page structure                                |
| `src/player.py`       | Display formatting and the play request handed to the player    |
| `src/callbacks/`      | Callbacks grouped by area: profile, browse, billboard, playback |
| `assets/chapflix.css` | The theme, using BEM class names                                |
| `assets/chapflix.js`  | Clientside callbacks for playback                               |

Dash loads everything in `assets/` automatically.

## Playback and the up-next countdown

The `<video>` element is rendered once and never replaced; starting playback only
changes its `src`. `EventListener` attaches its listeners to its children when it
mounts, so replacing the video would silently stop pause and end events.

Each playback gets a `play_id`, and every piece of countdown state carries it so
state from an earlier playback can never act on the current one.

1. The browser handles `timeupdate` in `chapflix.js`. When fewer than ten seconds
   of the API `duration` remain on an episode, it writes `{play_id, seconds}` to
   `CountdownStore`, once per whole second.
2. The first countdown update for a playback makes the server look up the next
   episode once (`UpNextStore`).
3. The overlay renders in the browser. **Stay here** dismisses it for that
   playback (`DismissedStore`).
4. When the video ends, or **Play now** is pressed, the server plays the queued
   episode unless it was dismissed, and records the play.

Because the countdown follows the video's position, it pauses with the video and
disappears if you seek back. Films never count down.

Pauses are recorded with the file's `file_key`, except the pause browsers fire
on reaching the end. Resume asks the API for the pause in the last-played file,
so a pause in one file never sets the start point of another.

At the start or end of a show the API returns `null` for the previous or next
episode. That hides the matching billboard button and means no countdown appears;
API failures show a notice instead.

## Checks

Python code follows the repo's `ruff` and `ty` setup. JavaScript and CSS tooling
lives in this directory and needs Node 20 or later:

```bash
cd app
npm install
npm run lint     # prettier, eslint, stylelint
npm run format   # prettier --write
npm test         # unit tests for assets/chapflix.js
```

## Tests

All frontend tests live in `tests/frontend/`.

```bash
uv run pytest tests/frontend
```

The end-to-end tests drive Firefox through Playwright against a running app and
**dev** API, and record plays and pauses for the Chap profile:

```bash
uv run playwright install firefox
CHAPFLIX_E2E_APP_URL=http://127.0.0.1:8050 \
CHAPFLIX_E2E_API_URL=http://localhost:8043 \
uv run pytest tests/frontend/test_e2e_playback.py
```

Playwright's Firefox can't keep decoding H.264 after a seek, so these tests fake
the video's position and dispatch media events on the real video element. They
cover everything from the app's event listener onwards, but not the browser
playing through to the real end of a file.
