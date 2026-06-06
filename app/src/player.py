######################################################################
# The refactor has begun and there are some ideas that probably hold
# from the work that's been done so far. That said, there's more work
# and not everything that's been done so far ought to make it into the
# final version of this module. For example, LastPlayed probably should
# become generalised so that it's applicable for the get_next_episode,
# get_previous_episode methods and others.
# The basic idea is to centralise repeated logic into functions that
# belong at the module level. The class becomes minimised and as far as
# possible methods should not be coupled. Where multiple methods do
# require coupling this should happen in a dedicated method so that
# each one can be tested in isolation thus giving confidence that the
# method for coupling is robust.
######################################################################
from typing import Optional, NamedTuple
from pathlib import Path
from datetime import datetime
from app.src.dbutils import execute_query, execute_statement
from app.src.content import MEDIA_FILES


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

User = NamedTuple("User", [("id_", int), ("name", str)])


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
    file_data = execute_query(f"select file_key from content where file = '{file}'")
    file_key = file_data[0][0]
    return int(file_key)


def drop_down_lists(lst: list[str]) -> list[dict[str, str]]:
    return [{"label": x, "value": x} for x in lst]


def create_display_string(): ...


class Player:
    user_id: Optional[int]
    user_display_name: Optional[str]
    current_selection: Optional[str]
    current_play_num: Optional[int]
    last_played_key: Optional[int]
    last_played_name: Optional[str]
    last_played_file: Optional[Path]
    playable_films: list[dict[str, str]]
    playable_shows: list[dict[str, str]]

    def __init__(self) -> None:
        # explicit runtime initialisation; cheap and clear
        self.user_id = None
        self.user_display_name = None
        self.current_selection = None
        self.current_play_num = None
        self.last_played_key = None
        self.last_played_name = None
        self.last_played_file = None
        self.playable_films = []
        self.playable_shows = []

        # safe to call these if they don't rely on other attributes being set
        # self.set_playable_films()
        # self.set_playable_shows()

    def set_user(self, display_name: str) -> None:
        self.user = get_user(display_name)

    def set_current_selection(self) -> None:
        last_played = get_last_played(self.user.id_)
        if last_played.media_type == "film":
            self.current_selection = last_played.film
        self.current_selection = f"{last_played.show}, season {last_played.season} episode {last_played.episode}"

    def set_last_played_attributes(self, last_played: LastPlayed) -> None:
        if last_played.media_type == "film":
            self.last_played_name = last_played.film
        else:
            self.last_played_name = f"{last_played.show} - Season {last_played.season} Episode {last_played.episode}"
        self.last_played_file = _format_filepath(Path(last_played.file))

    def get_last_played_string(self) -> str:
        ######################################################################
        # I still don't like that this method is coupled to set_last_played
        # but for now at least the logic is separated into a different method.
        # Revisit this coupling further into the refactor and see if there's
        # a cleaner, uncoupled approach.
        ######################################################################
        last_played = get_last_played(self.user.id_)
        self.set_last_played_attributes(last_played)
        if last_played.media_type == "film":
            if last_played.film:
                return last_played.film

        if last_played.show:
            return last_played.show

        raise Exception(
            "This exception won't ever get called and only exists to satisfy pre-commit. Plus, this method is being refactored anyway."
        )

    def record_played_file(self, file: Path) -> None:
        playtime = datetime.now()
        file_key = get_file_key(file)
        execute_statement(
            f"""
            INSERT INTO history (file_key, time, user_id) VALUES ({file_key}, '{playtime}', {self.user.id_})
            """
        )
        self.set_latest_play_num()

    def set_latest_play_num(self) -> None:
        play_num_data = execute_query(
            f"select play_num from history where user_id = {self.user.id_} order by time desc limit 1"
        )
        self.current_play_num = int(play_num_data[0][0])

    def record_paused_file(self, seconds: float) -> None:
        execute_statement(
            f"insert into paused_content (play_num, user_id, video_progress) values ({self.current_play_num}, {self.user.id_}, {seconds})"
        )

    def get_show_path(self, show: str, season: int, episode: int) -> Path:
        file_data = execute_query(
            f"select * from get_show_path('{show}', {season}, {episode})"
        )
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        self.set_current_selection()
        return _format_filepath(filepath)

    def get_film_path(self, film: str) -> Path:
        file_data = execute_query(f"select * from get_film_path('{film}')")
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        self.set_current_selection()
        return _format_filepath(filepath)

    def drop_down_lists(self, lst: list[str]) -> list[dict[str, str]]:
        return [{"label": x, "value": x} for x in lst]

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

    def get_selection_last_played(self, selection: str) -> str:
        selection_data = execute_query(f"select * from get_show('{selection}');")
        if len(selection_data) == 0:
            return "Show has not been watched, start from the beginning!"
        return f"{selection_data[0][0]}, Season {selection_data[0][1]} Episode {selection_data[0][2]}"

    def get_continue_watching_from(self) -> float:
        seconds_data = execute_query(
            f"select video_progress from paused_content where user_id = {self.user.id_} order by play_num desc, video_progress desc limit 1"
        )
        return seconds_data[0][0]

    def get_continue_watching(self) -> tuple[Path | None, str | None]:
        last_played = get_last_played(self.user.id_)
        if last_played.media_type == "film":
            return None, None

        display_string = f"Now playing: {last_played.show} Season {last_played.season} episode {last_played.episode}"
        path = Path(last_played.file)
        self.record_played_file(path)
        self.set_current_selection()
        return _format_filepath(path), display_string

    def get_next_episode(self) -> tuple[Path | None, str]:
        next_episode_data = execute_query(
            f"select * from get_next_episode({self.user.id_})"
        )
        next_episode_path = next_episode_data[0][0]
        if next_episode_path:
            show = next_episode_data[0][1]
            season = next_episode_data[0][2]
            episode = next_episode_data[0][3]
            display_string = f"Now playing: {show} season {season}, episode {episode}"
            self.record_played_file(next_episode_path)
            self.set_current_selection()
            return _format_filepath(next_episode_path), display_string
        return None, "There is nothing left to play! Time to pick another show."

    def get_previous_episode(self) -> tuple[Path | None, str]:
        previous_episode_data = execute_query(
            f"select * from get_previous_episode({self.user.id_})"
        )
        previous_episode_path = previous_episode_data[0][0]
        if previous_episode_path:
            show = previous_episode_data[0][1]
            season = previous_episode_data[0][2]
            episode = previous_episode_data[0][3]
            display_string = f"Now playing: {show} season {season}, episode {episode}"
            self.record_played_file(previous_episode_path)
            self.set_current_selection()
            return _format_filepath(previous_episode_path), display_string
        return None, "There is nothing left to play! Time to pick another show."


if __name__ == "__main__":
    player = Player()
