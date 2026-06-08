from typing import Literal, Optional, NamedTuple
from pathlib import Path
from datetime import datetime
from app.src.dbutils import execute_query, execute_statement
from app.src.content import MEDIA_FILES


class AutoPlayError(RuntimeError):
    pass


class MissingFileKey(RuntimeError):
    pass


LastPlayed = NamedTuple(
    "LastPlayed",
    [
        ("media_type", str),
        ("file_key", int),
        ("film", Optional[str]),
        ("show", Optional[str]),
        ("season", Optional[int]),
        ("episode", Optional[int]),
        ("file", str),
    ],
)

AutoPlayed = NamedTuple(
    "AutoPlayed", [("file", str), ("show", str), ("season", int), ("episode", int)]
)

User = NamedTuple("User", [("id_", int), ("name", str)])


def _get_filekeys() -> dict[Path, int]:
    file_keys_data = execute_query("select * from content;")
    return {Path(x[1]): int(x[0]) for x in file_keys_data}


FILE_KEYS = _get_filekeys()


def _format_filepath(path: Path) -> Path:
    return path.relative_to(MEDIA_FILES.parent)


def get_last_played(user_id: int) -> LastPlayed:
    last_played_data = execute_query(f"select * from get_last_played({user_id});")
    last_played_values = last_played_data[0]
    return LastPlayed(*last_played_values)


def get_user(display_name: str) -> User:
    user_id_data = execute_query(
        f"select user_id from users where display_name = '{display_name}';"
    )
    user_id = int(user_id_data[0][0])
    return User(user_id, display_name)


def get_file_key(file: Path) -> int:
    key = FILE_KEYS.get(file)
    if key is not None:
        return key
    raise MissingFileKey(
        f"{file.relative_to(file.parent)} does not have a corresponding key"
    )


def drop_down_lists(lst: list[str]) -> list[dict[str, str]]:
    return [{"label": x, "value": x} for x in lst]


def get_auto_play(
    previous_or_next: Literal["previous", "next"], user: User
) -> AutoPlayed:
    match previous_or_next:
        case "previous":
            data = execute_query(f"select * from get_previous_episode({user.id_});")
        case "next":
            data = execute_query(f"select * from get_next_episode({user.id_});")
    values = data[0]
    return AutoPlayed(*values)


def format_auto_play_string(playing: AutoPlayed | LastPlayed) -> str:
    return f"Now playing: {playing.show} season {playing.season}, episode {playing.episode}"


def get_play_num(user: User) -> int:
    play_num_data = execute_query(
        f"select play_num from history where user_id = {user.id_} order by time desc limit 1"
    )
    return int(play_num_data[0][0])


class Player:
    _user: Optional[User]
    _last_played: Optional[LastPlayed]
    current_selection: Optional[str]
    current_play_num: int
    playable_films: list[dict[str, str]]
    playable_shows: list[dict[str, str]]

    def __init__(self) -> None:
        self._user = None
        self._last_played = None
        self.current_selection = None
        self.current_play_num = 0
        self.playable_films = []
        self.playable_shows = []

        self.set_playable_films()
        self.set_playable_shows()

    @property
    def user(self) -> User:
        if self._user is None:
            raise RuntimeError(
                "User has not been set. A user must be set before proceeding."
            )
        return self._user

    @user.setter
    def user(self, display_name: str) -> None:
        self._user = get_user(display_name)
        self.current_play_num = get_play_num(self._user)

    @property
    def last_played(self) -> LastPlayed:
        if self._last_played is None:
            raise RuntimeError(
                "Last played cannot be determined by user selection. A user must be set before proceeding."
            )
        return self._last_played

    @last_played.setter
    def last_played(self, user: User) -> None:
        self._last_played = get_last_played(user.id_)
        self._set_last_played_attributes()

    def get_film_options(self) -> list[str]:
        film_data = execute_query("select distinct film from films")
        return sorted([x[0] for x in film_data])

    def get_show_options(self) -> list[str]:
        show_data = execute_query("select distinct show from shows")
        return sorted([x[0] for x in show_data])

    def get_season_options(self, show: str) -> list[int]:
        seasons_data = execute_query(
            f"select distinct season from shows where show = '{show}' order by season"
        )
        return [x[0] for x in seasons_data]

    def get_episode_options(self, show: str, season: int) -> list[int]:
        episodes_data = execute_query(
            f"select distinct episode from shows where show = '{show}' and season = {season} order by episode"
        )
        return [x[0] for x in episodes_data]

    def set_playable_films(self) -> None:
        """Sets the attribute for the app's initial dropdown list of playable films"""
        self.playable_films = drop_down_lists(self.get_film_options())

    def set_playable_shows(self) -> None:
        """Sets the attribute for the app's initial dropdown list of playable shows"""
        self.playable_shows = drop_down_lists(self.get_show_options())

    def _set_last_played_attributes(self) -> None:
        match self.last_played.media_type:
            case "film":
                self.last_played_name = self.last_played.film
            case "show":
                self.last_played_name = format_auto_play_string(self.last_played)
        self.last_played_file = _format_filepath(Path(self.last_played.file))

    def set_current_selection(self) -> None:
        last_played = get_last_played(self.user.id_)
        # The below line feels odd because it looks like it's setting one
        # attribute as a reference to another but the last_played attribute
        # is a property with a setter which must be passed the user attribute.
        self.last_played = self.user
        match self.last_played.media_type:
            case "film":
                self.current_selection = last_played.film
            case "show":
                self.current_selection = format_auto_play_string(last_played)

    def get_last_played_string(self) -> str:
        self._set_last_played_attributes()
        if self.last_played_name:
            return self.last_played_name

        raise RuntimeError("Last played string cannot be empty")

    def record_played_file(self, file: Path) -> None:
        playtime = datetime.now()
        file_key = get_file_key(file)
        execute_statement(
            f"""
            INSERT INTO history (file_key, time, user_id) VALUES ({file_key}, '{playtime}', {self.user.id_})
            """
        )
        self.current_play_num += 1

    def record_paused_file(self, seconds: float) -> None:
        execute_statement(
            f"insert into paused_content (play_num, user_id, video_progress) values ({self.current_play_num}, {self.user.id_}, {seconds})"
        )

    def get_show_path(self, show: str, season: int, episode: int) -> Path:
        file_data = execute_query(
            f"select * from get_show_path('{show}', {season}, {episode})"
        )
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)  # Write to history table
        self.set_current_selection()  # Reads from history table
        return _format_filepath(filepath)

    def get_film_path(self, film: str) -> Path:
        file_data = execute_query(f"select * from get_film_path('{film}')")
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)  # Write to history table
        self.set_current_selection()  # Reads from history table
        return _format_filepath(filepath)

    def get_continue_watching_from(self) -> float:
        seconds_data = execute_query(
            f"select video_progress from paused_content where user_id = {self.user.id_} order by play_num desc, video_progress desc limit 1"
        )
        return seconds_data[0][0]

    def get_continue_watching(self) -> tuple[Path | None, str | None]:
        last_played = get_last_played(self.user.id_)
        if last_played.media_type == "film":
            return None, None

        display_string = format_auto_play_string(last_played)
        path = Path(last_played.file)
        self.record_played_file(path)
        self.set_current_selection()
        return _format_filepath(path), display_string

    def get_next_episode(self) -> tuple[Path | None, str]:
        auto_played = get_auto_play("next", self.user)
        if auto_played.file:
            self.record_played_file(Path(auto_played.file))
            self.set_current_selection()
            return _format_filepath(Path(auto_played.file)), format_auto_play_string(
                auto_played
            )

        return None, "There is nothing left to play! Time to pick another show."

    def get_previous_episode(self) -> tuple[Path | None, str]:
        auto_played = get_auto_play("previous", self.user)
        if auto_played.file:
            self.record_played_file(Path(auto_played.file))
            self.set_current_selection()
            return _format_filepath(Path(auto_played.file)), format_auto_play_string(
                auto_played
            )

        return None, "There is nothing left to play! Time to pick another show."
