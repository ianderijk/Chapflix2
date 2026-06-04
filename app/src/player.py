from typing import Optional
from pathlib import Path
from datetime import datetime
from app.src.dbutils import execute_query, execute_statement


class Player:
    def __init__(self):
        self.set_playable_films()
        self.set_playable_shows()
        self.user_id: Optional[int] = None
        self.current_selection: Optional[str] = None

    def format_filepath(self, path: Path) -> str:
        """Path object converted to a string so it can be made relative"""
        path_list = str(path).split("/")
        trimmed_path = "/".join(path_list[path_list.index("content") :])
        return trimmed_path

    def set_user(self, display_name: str) -> None:
        user_id_data = execute_query(
            f"select user_id from users where display_name = '{display_name}'"
        )
        self.user_id = int(user_id_data[0][0])
        self.user_display_name = display_name

    def set_current_selection(self) -> None:
        data = execute_query(f"select * from get_last_played({self.user_id})")
        media_type = data[0][0]
        if media_type == "film":
            self.current_selection = data[0][2]
            return
        show: str = data[0][3]
        season: int = data[0][4]
        episode: int = data[0][5]
        self.current_selection = f"{show}, season {season} episode {episode}"

    def get_last_played(self) -> str:
        """Sets both the last played file name and key. When last played is a show
        the string is formatted to include the show name, season number and episode.
        Films are returned as a string of the film name. File key attribute is simply
        the relevant file key regardless of content type"""
        last_played_data = execute_query(
            f"select * from get_last_played({self.user_id})"
        )
        self.last_played_key = last_played_data[0][1]
        if last_played_data[0][0] == "film":
            self.last_played_name = str(last_played_data[0][2])
            self.last_played_file = self.format_filepath(last_played_data[0][6])
        else:
            show = str(last_played_data[0][3])
            season = last_played_data[0][4]
            episode = last_played_data[0][5]
            self.last_played_name = (
                f"{show.title()} - Season {season} Episode {episode}"
            )
            self.last_played_file = self.format_filepath(last_played_data[0][6])
        self.set_current_selection()
        return self.last_played_name

    def set_latest_play_num(self) -> None:
        play_num_data = execute_query(
            f"select play_num from history where user_id = {self.user_id} order by time desc limit 1"
        )
        self.current_play_num = play_num_data[0][0]

    def record_played_file(self, file: Path) -> None:
        playtime = datetime.now()
        file_data = execute_query(f"select file_key from content where file = '{file}'")
        file_key = file_data[0][0]
        execute_statement(
            f"""
            INSERT INTO history (file_key, time, user_id) VALUES ({file_key}, '{playtime}', {self.user_id})
            """
        )
        self.set_latest_play_num()

    def record_paused_file(self, seconds: float) -> None:
        execute_statement(
            f"insert into paused_content (play_num, user_id, video_progress) values ({self.current_play_num}, {self.user_id}, {seconds})"
        )

    def get_show_path(self, show: str, season: int, episode: int) -> str:
        file_data = execute_query(
            f"select * from get_show_path('{show}', {season}, {episode})"
        )
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        self.set_current_selection()
        return self.format_filepath(filepath)

    def get_film_path(self, film) -> str:
        file_data = execute_query(f"select * from get_film_path('{film}')")
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        self.set_current_selection()
        return self.format_filepath(filepath)

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
        self.playable_films = self.drop_down_lists(self.get_film_options())

    def set_playable_shows(self) -> None:
        """Sets the attribute for the app's initial dropdown list of playable films"""
        self.playable_shows = self.drop_down_lists(self.get_show_options())

    def get_selection_last_played(self, selection: str) -> str:
        selection_data = execute_query(f"select * from get_show('{selection}');")
        if len(selection_data) == 0:
            return "Show has not been watched, start from the beginning!"
        return f"{selection_data[0][0]}, Season {selection_data[0][1]} Episode {selection_data[0][2]}"

    def get_continue_watching_from(self) -> float:
        seconds_data = execute_query(
            f"select video_progress from paused_content where user_id = {self.user_id} order by play_num desc, video_progress desc limit 1"
        )
        return seconds_data[0][0]

    def get_continue_watching(self) -> tuple[str | None, str | None]:
        last_played_data = execute_query(
            f"select * from get_last_played({self.user_id})"
        )
        media_type = last_played_data[0][0]
        if media_type == "film":
            return None, None
        episode_path = last_played_data[0][6]
        show = last_played_data[0][3]
        season = last_played_data[0][4]
        episode = last_played_data[0][5]
        display_string = f"Now playing: {show} Season {season} episode {episode}"
        self.record_played_file(episode_path)
        self.set_current_selection()
        return self.format_filepath(episode_path), display_string

    def get_next_episode(self) -> tuple[str | None, str]:
        next_episode_data = execute_query(
            f"select * from get_next_episode({self.user_id})"
        )
        next_episode_path = next_episode_data[0][0]
        if next_episode_path:
            show = next_episode_data[0][1]
            season = next_episode_data[0][2]
            episode = next_episode_data[0][3]
            display_string = f"Now playing: {show} season {season}, episode {episode}"
            self.record_played_file(next_episode_path)
            self.set_current_selection()
            return self.format_filepath(next_episode_path), display_string
        return None, "There is nothing left to play! Time to pick another show."

    def get_previous_episode(self) -> tuple[str | None, str]:
        previous_episode_data = execute_query(
            f"select * from get_previous_episode({self.user_id})"
        )
        previous_episode_path = previous_episode_data[0][0]
        if previous_episode_path:
            show = previous_episode_data[0][1]
            season = previous_episode_data[0][2]
            episode = previous_episode_data[0][3]
            display_string = f"Now playing: {show} season {season}, episode {episode}"
            self.record_played_file(previous_episode_path)
            self.set_current_selection()
            return self.format_filepath(previous_episode_path), display_string
        return None, "There is nothing left to play! Time to pick another show."
