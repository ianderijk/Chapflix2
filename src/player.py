from __future__ import annotations
from pathlib import Path
from datetime import datetime
from .dbconn import execute_query, execute_statement


class Player:
    def __init__(self):
        self.set_playable_films()
        self.set_playable_shows()
        self.set_last_played()

    def set_last_played(self) -> None:
        """Sets both the last played file name and key. When last played is a show
        the string is formatted to include the show name, season number and episode.
        Films are returned as a string of the film name. File key attribute is simply
        the relevant file key regardless of content type"""
        last_played_data = execute_query(
            """
            select case when f.film is not null then 'film' else 'show' end [media_type]
                ,coalesce(f.file_key, s.file_key) [file_key]
                ,f.film
                ,s.show
                ,s.season
                ,s.episode
            from history h
            left join shows s on h.file_key = s.file_key
            left join films f on h.file_key = f.file_key
            order by [time] desc
            limit 1
            """
        )
        self.last_played_key = last_played_data[0][1]
        if last_played_data[0][0] == "film":
            self.last_played_name = str(last_played_data[0][2])
        else:
            show = str(last_played_data[0][3])
            season = last_played_data[0][4]
            episode = last_played_data[0][5]
            self.last_played_name = (
                f"{show.title()} - Season {season} Episode {episode}"
            )

    def record_played_file(self, file: Path) -> None:
        playtime = datetime.now()
        file_data = execute_query(f"select file_key from content where file = '{file}'")
        file_key = file_data[0][0]
        execute_statement(
            f"""
            INSERT INTO history (file_key, time) VALUES ({file_key}, '{playtime}')
            """
        )

    def format_filepath(self, path: Path) -> str:
        path_list = str(path).split("/")
        return "/".join(path_list[path_list.index("assets") :])

    def get_show_path(self, show: str, season: int, episode: int) -> str:
        file_data = execute_query(
            f"""
            select c.file
            from shows s
            left join content c on s.file_key = c.file_key
            where s.show = '{show}'
                and s.season = {season}
                and s.episode = {episode}
            """
        )
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        return self.format_filepath(filepath)

    def get_film_path(self, film) -> str:
        file_data = execute_query(
            f"""
            select c.file
            from films f
            left join content c on f.file_key = c.file_key
            where f.film = '{film}'
            """
        )
        filepath = Path(file_data[0][0])
        self.record_played_file(filepath)
        return self.format_filepath(filepath)

    def drop_down_lists(self, lst: list) -> list:
        return [{"label": x, "value": x} for x in lst]

    def get_film_options(self) -> list:
        film_data = execute_query("select distinct film from films")
        return [x[0] for x in film_data]

    def get_show_options(self) -> list:
        show_data = execute_query("select distinct show from shows")
        return [x[0] for x in show_data]

    def get_season_options(self, show: str) -> list:
        seasons_data = execute_query(
            f"select distinct season from shows where show = '{show}' order by season"
        )
        return [x[0] for x in seasons_data]

    def get_episode_options(self, show: str, season: int) -> list:
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


if __name__ == "__main__":
    print("hello from player.py")
