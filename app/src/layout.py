from pathlib import Path

from dash import dcc, html
from dash_extensions import EventListener

from app.src.player import card_palette, pretty_title

USERS = ["Lady", "Chap"]
COUNTDOWN_SECONDS = 10

ID_TOP = "top"
ID_USER_STORE = "UserStore"
ID_CATALOGUE_STORE = "CatalogueStore"
ID_SHOW_SELECTION_STORE = "ShowSelectionStore"
ID_PLAY_REQUEST_STORE = "PlayRequestStore"
ID_UP_NEXT_STORE = "UpNextStore"
ID_REDUNDANT_STORE = "RedundantOutputStore"
ID_COUNTDOWN = "Countdown"

ID_GATE = "ProfileGate"
ID_PROFILE_NAME = "ProfileName"
ID_SWITCH_PROFILE = "SwitchProfile"
ID_SEARCH = "Search"
ID_NOTICE = "Notice"

ID_THEATRE = "Theatre"
ID_NOW_PLAYING_TITLE = "NowPlayingTitle"
ID_NOW_PLAYING_SUBTITLE = "NowPlayingSubtitle"
ID_NOW_PLAYING_META = "NowPlayingMeta"
ID_VIDEO_CONTAINER = "VideoContainer"
ID_VIDEO_EVENTS = "VideoEvents"
ID_PLAYER = "Player"

ID_UP_NEXT = "UpNext"
ID_UP_NEXT_TITLE = "UpNextTitle"
ID_UP_NEXT_COUNT = "UpNextCount"
ID_UP_NEXT_PLAY = "UpNextPlay"
ID_UP_NEXT_CANCEL = "UpNextCancel"

ID_BILLBOARD = "Billboard"
ID_HERO_KICKER = "HeroKicker"
ID_HERO_TITLE = "HeroTitle"
ID_HERO_SUBTITLE = "HeroSubtitle"
ID_HERO_META = "HeroMeta"
ID_HERO_RESUME = "HeroResume"
ID_HERO_PREV = "HeroPrevious"
ID_HERO_NEXT = "HeroNext"

ID_SHOWS_ROW = "ShowsRow"
ID_FILMS_ROW = "FilmsRow"
ID_SHOW_PANEL = "ShowPanel"

TYPE_PROFILE = "profile"
TYPE_SHOW_CARD = "show-card"
TYPE_FILM_CARD = "film-card"
TYPE_SEASON_TAB = "season-tab"
TYPE_EPISODE_TILE = "episode-tile"

ORNAMENT = "✠"


def video_player(file: Path | str | None) -> EventListener:
    """The EventListener always exists so its callbacks have something to bind to."""
    children = []
    if file:
        children = [
            html.Video(
                controls=True,
                id=ID_PLAYER,
                src=str(file),
                autoPlay=True,
                className="theatre__video",
            )
        ]
    return EventListener(
        id=ID_VIDEO_EVENTS,
        events=[
            {"event": "pause", "props": ["target.currentTime"]},
            {"event": "loadedmetadata"},
            {"event": "ended", "props": ["type"]},
        ],
        logging=True,
        children=children,
    )


def build_stores() -> html.Div:
    return html.Div(
        children=[
            dcc.Store(id=ID_USER_STORE, storage_type="session"),
            dcc.Store(id=ID_CATALOGUE_STORE),
            dcc.Store(id=ID_SHOW_SELECTION_STORE),
            dcc.Store(id=ID_PLAY_REQUEST_STORE),
            dcc.Store(id=ID_UP_NEXT_STORE),
            dcc.Store(id=ID_REDUNDANT_STORE, storage_type="session"),
            dcc.Interval(id=ID_COUNTDOWN, interval=1000, disabled=True),
        ]
    )


def build_profile_gate() -> html.Div:
    return html.Div(
        id=ID_GATE,
        className="gate",
        children=[
            html.Div(className="gate__logo", children="Chapflix"),
            html.H1("Who's watching?", className="gate__title"),
            html.Div(
                className="gate__profiles",
                children=[
                    html.Button(
                        id={"type": TYPE_PROFILE, "index": user},
                        className="profile",
                        style=_palette_style(user),
                        children=[
                            html.Span(user[0], className="profile__initial"),
                            html.Span(user, className="profile__name"),
                        ],
                    )
                    for user in USERS
                ],
            ),
        ],
    )


def build_navbar() -> html.Header:
    return html.Header(
        className="navbar",
        children=[
            html.A("Chapflix", href=f"#{ID_TOP}", className="navbar__logo"),
            html.Nav(
                className="navbar__links",
                children=[
                    html.A("Home", href=f"#{ID_TOP}"),
                    html.A("Shows", href="#shows"),
                    html.A("Films", href="#films"),
                ],
            ),
            dcc.Input(
                id=ID_SEARCH,
                type="search",
                placeholder="Search the vaults…",
                debounce=True,
                className="navbar__search",
            ),
            html.Div(
                className="navbar__profile",
                children=[
                    html.Span(id=ID_PROFILE_NAME, className="navbar__profile-name"),
                    html.Button(
                        "Switch", id=ID_SWITCH_PROFILE, className="btn btn--ghost"
                    ),
                ],
            ),
        ],
    )


def build_theatre() -> html.Section:
    return html.Section(
        id=ID_THEATRE,
        className="theatre theatre--idle",
        children=[
            html.Div(
                className="theatre__header",
                children=[
                    html.Span("Now playing", className="kicker"),
                    html.H2(id=ID_NOW_PLAYING_TITLE, className="theatre__title"),
                    html.Div(id=ID_NOW_PLAYING_SUBTITLE, className="theatre__subtitle"),
                    html.Div(id=ID_NOW_PLAYING_META, className="meta"),
                ],
            ),
            html.Div(
                className="theatre__stage",
                children=[
                    html.Div(id=ID_VIDEO_CONTAINER, children=video_player(None)),
                    build_up_next(),
                ],
            ),
        ],
    )


def build_up_next() -> html.Div:
    return html.Div(
        id=ID_UP_NEXT,
        className="up-next",
        children=[
            html.Span("Up next", className="kicker"),
            html.Div(id=ID_UP_NEXT_TITLE, className="up-next__title"),
            html.Div(id=ID_UP_NEXT_COUNT, className="up-next__count"),
            html.Div(
                className="up-next__actions",
                children=[
                    html.Button(
                        "▶ Play now", id=ID_UP_NEXT_PLAY, className="btn btn--blood"
                    ),
                    html.Button(
                        "Stay here", id=ID_UP_NEXT_CANCEL, className="btn btn--ghost"
                    ),
                ],
            ),
        ],
    )


def build_billboard() -> html.Section:
    return html.Section(
        id=ID_BILLBOARD,
        className="billboard",
        children=[
            html.Div(
                className="billboard__content",
                children=[
                    html.Span(id=ID_HERO_KICKER, className="kicker"),
                    html.H1(id=ID_HERO_TITLE, className="billboard__title"),
                    html.Div(id=ID_HERO_SUBTITLE, className="billboard__subtitle"),
                    html.Div(id=ID_HERO_META, className="meta"),
                    html.Div(
                        className="billboard__actions",
                        children=[
                            html.A(
                                "▶ Resume",
                                id=ID_HERO_RESUME,
                                href=f"#{ID_TOP}",
                                className="btn btn--hidden",
                            ),
                            html.A(
                                id=ID_HERO_PREV,
                                href=f"#{ID_TOP}",
                                className="btn btn--hidden",
                            ),
                            html.A(
                                id=ID_HERO_NEXT,
                                href=f"#{ID_TOP}",
                                className="btn btn--hidden",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_row(title: str, anchor: str, row_id: str) -> html.Section:
    return html.Section(
        id=anchor,
        className="row",
        children=[
            html.H2(
                children=[html.Span(ORNAMENT, className="row__ornament"), title],
                className="row__title",
            ),
            html.Div(id=row_id, className="row__track"),
        ],
    )


def build_layout() -> html.Div:
    return html.Div(
        className="chapflix",
        children=[
            html.Div(id=ID_TOP),
            build_stores(),
            build_profile_gate(),
            build_navbar(),
            html.Main(
                children=[
                    build_theatre(),
                    build_billboard(),
                    html.Div(id=ID_NOTICE, className="notice"),
                    build_row("Shows", "shows", ID_SHOWS_ROW),
                    html.Section(id=ID_SHOW_PANEL, className="show-panel"),
                    build_row("Films", "films", ID_FILMS_ROW),
                ]
            ),
            html.Footer(
                className="footer",
                children=f"{ORNAMENT}  Chapflix  {ORNAMENT}",
            ),
        ],
    )


def _palette_style(name: str) -> dict[str, str]:
    light, dark = card_palette(name)
    return {"--card-light": light, "--card-dark": dark}


def title_card(name: str, card_type: str, href: str) -> html.A:
    title = pretty_title(name)
    return html.A(
        id={"type": card_type, "index": name},
        href=href,
        className="card",
        style=_palette_style(name),
        title=title,
        children=[
            html.Span(title[0], className="card__initial"),
            html.Span(title, className="card__title"),
        ],
    )


def build_cards(names: list[str], card_type: str, href: str) -> list[html.A] | html.P:
    if not names:
        return html.P("Nothing lurks here.", className="empty")
    return [title_card(name, card_type, href) for name in names]


def build_show_panel(
    show: str,
    seasons: list[int],
    season: int | None,
    episodes: list[int],
    last_watched: int | None,
    up_next: int | None,
) -> list:
    return [
        html.Div(
            className="show-panel__header",
            children=[
                html.Span("Now browsing", className="kicker"),
                html.H2(pretty_title(show), className="show-panel__title"),
            ],
        ),
        html.Div(
            className="season-tabs",
            children=[
                html.Button(
                    f"Season {number}",
                    id={"type": TYPE_SEASON_TAB, "index": number},
                    className="season-tab"
                    + (" season-tab--active" if number == season else ""),
                )
                for number in seasons
            ],
        ),
        html.Div(
            className="episodes",
            children=[
                _episode_tile(number, last_watched, up_next) for number in episodes
            ],
        ),
    ]


def _episode_tile(number: int, last_watched: int | None, up_next: int | None) -> html.A:
    class_name = "episode"
    marker = None
    if number == last_watched:
        class_name += " episode--last"
        marker = "Last watched"
    elif number == up_next:
        class_name += " episode--next"
        marker = "Up next"
    return html.A(
        id={"type": TYPE_EPISODE_TILE, "index": number},
        href=f"#{ID_TOP}",
        className=class_name,
        children=[
            html.Span(f"{number:02}", className="episode__number"),
            html.Span("Episode", className="episode__label"),
            html.Span(marker, className="episode__marker") if marker else None,
        ],
    )
