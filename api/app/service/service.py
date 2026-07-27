from fastapi import HTTPException
from utils.dbutils import execute_query
from api.app.models.user import User
from api.app.models.last_played import LastPlayed
from api.app.models.auto_play import AutoPlay
from api.app.models.content import Films, Shows, Seasons, Episodes, Film, Episode


def get_user(username: str) -> User:
    query = "select * from users where display_name = :display_name;"
    params = {"display_name": username}
    data = execute_query(query, params)
    if not data:
        raise HTTPException(status_code=404, detail=f"User: {username} not found")
    values = data[0]
    user = User(id_=values[0], name=values[1])
    return user


def get_last_played(user: User) -> LastPlayed:
    query = "select * from get_last_played(:user_id);"
    params = {"user_id": user.id_}
    data = execute_query(query, params)
    values = data[0]
    last_played = LastPlayed(
        media_type=values[0],
        file_key=values[1],
        film=values[2],
        show=values[3],
        season=values[4],
        episode=values[5],
        file=values[6],
    )
    return last_played


def get_next_episode(user: User) -> AutoPlay:
    query = "select * from get_next_episode(:user_id);"
    params = {"user_id": user.id_}
    data = execute_query(query, params)
    values = data[0]
    next_episode = AutoPlay(
        file=values[0],
        show=values[1],
        season=values[2],
        episode=values[3],
    )
    return next_episode


def get_previous_episode(user: User) -> AutoPlay:
    query = "select * from get_previous_episode(:user_id);"
    params = {"user_id": user.id_}
    data = execute_query(query, params)
    values = data[0]
    previous_episode = AutoPlay(
        file=values[0],
        show=values[1],
        season=values[2],
        episode=values[3],
    )
    return previous_episode


def get_films() -> Films:
    query = "select film from films;"
    data = execute_query(query)
    values = sorted([x[0] for x in data])
    films = Films(films=values)
    return films


def get_film(film: str) -> Film:
    query = "select f.film, c.file from films f left join content c on f.file_key = c.file_key where f.film= :film;"
    params = {"film": film}
    data = execute_query(query, params)
    values = data[0]
    selection = Film(name=values[0], file=values[1])
    return selection


def get_shows() -> Shows:
    query = "select distinct show from shows;"
    data = execute_query(query)
    values = sorted([x[0] for x in data])
    shows = Shows(shows=values)
    return shows


def get_seasons(show: str) -> Seasons:
    query = "select distinct season from shows where show = :show;"
    params = {"show": show}
    data = execute_query(query, params)
    values = sorted([x[0] for x in data])
    seasons = Seasons(seasons=values)
    return seasons


def get_episodes(show: str, season: int) -> Episodes:
    query = "select episode from shows where show = :show and season = :season;"
    params = {"show": show, "season": season}
    data = execute_query(query, params)
    values = sorted([x[0] for x in data])
    episodes = Episodes(episodes=values)
    return episodes


def get_episode(show: str, season: int, episode: int) -> Episode:
    query = """
        select s.show, s.season, s.episode, c.file
        from shows s
        left join content c on s.file_key = c.file_key
        where s.show = :show
            and s.season = :season
            and s.episode = :episode
        ;
        """
    params = {"show": show, "season": season, "episode": episode}
    data = execute_query(query, params)
    values = data[0]
    selection = Episode(
        show=values[0],
        season=values[1],
        episode=values[2],
        file=values[3],
    )
    return selection
