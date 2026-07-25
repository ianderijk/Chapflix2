from typing import Literal, Optional, NamedTuple
from pathlib import Path
from datetime import datetime
import re
from app.src.dbutils import execute_query, execute_statement
from app.src.content import MEDIA_FILES, ContentType


class AutoPlayError(RuntimeError):
    pass


class MissingFileKey(RuntimeError):
    pass


class InvalidSelectionError(RuntimeError):
    pass


class LastPlayed(NamedTuple):
    media_type: str
    file_key: str
    film: str | None
    show: str | None
    season: int | None
    episode: int | None
    file: str


class AutoPlayed(NamedTuple):
    file: str | None
    show: str | None
    season: int | None
    episode: int | None


class SelectionData(NamedTuple):
    file: Path
    plays: int | None
    last_played: datetime | None
    show: str | None
    season: int | None
    episode: int | None
    film: str | None


class User(NamedTuple):
    id_: int
    name: str


def _get_filekeys() -> dict[Path, int]:
    file_keys_data = execute_query("select * from content;")
    return {Path(x[1]): int(x[0]) for x in file_keys_data}


FILE_KEYS = _get_filekeys()


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


def get_play_num(user: User) -> int:
    play_num_data = execute_query(
        f"select play_num from history where user_id = {user.id_} order by time desc limit 1"
    )
    return int(play_num_data[0][0])


def _is_show(filename: str) -> bool:
    match_ = re.match(r"S(\d+)E(\d+)", filename)
    return bool(match_)


def get_file_content_types() -> dict[Path, ContentType]:
    files_data = execute_query("select file from content;")
    file_records = [x[0] for x in files_data]
    content_types = {}
    for record in file_records:
        path = Path(record)
        filename = path.stem
        if _is_show(filename):
            content_types[path] = ContentType.SHOW
        else:
            content_types[path] = ContentType.FILM
    return content_types


def get_selection_mappings() -> dict[str, Path]:
    data = execute_query("select * from get_file_mappings();")
    return {x[0]: Path(x[1]) for x in data}


CONTENT_TYPES = get_file_content_types()
SELECTION_MAPPINGS = get_selection_mappings()


class Selection:
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.service_filepath = self._format_filepath_for_service()
        self.content_type = self._get_content_type()
        self._selection_string = ""

    def _get_content_type(self) -> ContentType:
        return CONTENT_TYPES[self.filepath]

    def _get_show_selection(
        self, show: str, season: int, episode: int
    ) -> SelectionData:
        selection_values = execute_query(
            f"select * from get_show_path('{show}', {season}, {episode})"
        )
        self._selection_string = (
            f"Now playing: {show} season {season}, episode {episode}"
        )
        selection_data = list(selection_values[0]) + [show, season, episode, None]
        return SelectionData(*selection_data)

    def _get_film_selection(self, film: str) -> SelectionData:
        selection_values = execute_query(f"select * from get_film_path('{film}')")
        self._selection_string = f"Now playing: {film}"
        selection_data = list(selection_values[0]) + [None, None, None, film]
        return SelectionData(*selection_data)

    def _format_filepath_for_service(self) -> Path:
        return self.filepath.relative_to(MEDIA_FILES.parent)

    def get_selection_data(self, **kwargs) -> SelectionData:
        selection = None
        match self.content_type:
            case ContentType.SHOW:
                show = kwargs.get("show")
                season = kwargs.get("season")
                episode = kwargs.get("episode")
                if show and season and episode:
                    selection = self._get_show_selection(
                        show=show, season=season, episode=episode
                    )
            case ContentType.FILM:
                film = kwargs.get("film")
                if film:
                    selection = self._get_film_selection(film=film)

        if selection:
            return selection

        raise RuntimeError("Failed to match ContentType")

    def _format_play_timestamp(self, timestamp: datetime | None) -> str:
        if timestamp:
            return f"{timestamp.hour:02}:{timestamp.minute:02} {timestamp.day:02}-{timestamp.month:02}-{timestamp.year}"
        return "Never!"

    def get_display_string(self, selection: SelectionData) -> str:
        play_timestamp = self._format_play_timestamp(selection.last_played)
        play_information = (
            f"Last played: {play_timestamp} | Played {selection.plays} times"
        )
        display_string = self._selection_string + " | " + play_information
        return display_string


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
        self.last_played_name = self.get_last_played_string()
        self.last_played_file = (Path(self.last_played.file)).relative_to(
            MEDIA_FILES.parent
        )

    def get_last_played_string(self) -> str:
        last_played = f"{self.user.name} last watched "
        match self.last_played.media_type:
            case "film":
                return last_played + str(self.last_played.film)
            case "show":
                return (
                    last_played
                    + f"{self.last_played.show} season {self.last_played.season} episode {self.last_played.episode}"
                )
            case _:
                raise RuntimeError(
                    "Error occured displaying user's last played content"
                )

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

    def get_show_path(self, show: str, season: int, episode: int) -> tuple[Path, str]:
        filepath = SELECTION_MAPPINGS.get(f"{show}{season}{episode}")
        if not filepath:
            raise InvalidSelectionError(
                f"{show} Season {season} Episode {episode} does not exist!"
            )
        selection = Selection(filepath)
        self.record_played_file(filepath)
        selection_data = selection.get_selection_data(
            show=show, season=season, episode=episode
        )
        display_string = selection.get_display_string(selection_data)
        return selection.service_filepath, display_string

    def get_film_path(self, film: str) -> tuple[Path, str]:
        filepath = SELECTION_MAPPINGS.get(film)
        if not filepath:
            raise InvalidSelectionError(f"{film} does not exist!")
        selection = Selection(filepath)
        self.record_played_file(filepath)
        selection_data = selection.get_selection_data(film=film)
        display_string = selection.get_display_string(selection_data)
        return selection.service_filepath, display_string

    def get_continue_watching_from(self) -> float:
        seconds_data = execute_query(
            f"select video_progress from paused_content where user_id = {self.user.id_} order by play_num desc, video_progress desc limit 1"
        )
        return seconds_data[0][0]

    def get_continue_watching(self) -> tuple[Path | None, str | None]:
        last_played = get_last_played(self.user.id_)
        filepath = Path(last_played.file)
        selection = Selection(filepath)
        match selection.content_type:
            case ContentType.SHOW:
                selection_data = selection.get_selection_data(
                    show=last_played.show,
                    season=last_played.season,
                    episode=last_played.episode,
                )
            case ContentType.FILM:
                selection_data = selection.get_selection_data(film=last_played.film)
        display_string = selection.get_display_string(selection_data)
        self.record_played_file(filepath)
        return selection.service_filepath, display_string

    def get_next_episode(self) -> tuple[Path | None, str]:
        auto_played = get_auto_play("next", self.user)
        if auto_played.file is None:
            return None, "There is nothing left to play! Time to pick another show."
        filepath = Path(auto_played.file)
        selection = Selection(filepath)
        selection_data = selection.get_selection_data(
            show=auto_played.show,
            season=auto_played.season,
            episode=auto_played.episode,
        )
        display_string = selection.get_display_string(selection_data)
        self.record_played_file(filepath)
        return selection.service_filepath, display_string

    def get_previous_episode(self) -> tuple[Path | None, str]:
        auto_played = get_auto_play("previous", self.user)
        if auto_played.file is None:
            return None, "There is nothing left to play! Time to pick another show."
        filepath = Path(auto_played.file)
        selection = Selection(filepath)
        selection_data = selection.get_selection_data(
            show=auto_played.show,
            season=auto_played.season,
            episode=auto_played.episode,
        )
        display_string = selection.get_display_string(selection_data)
        self.record_played_file(filepath)
        return selection.service_filepath, display_string
