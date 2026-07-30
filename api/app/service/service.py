from fastapi import HTTPException
from utils.dbutils import execute_query
from api.app.models.user import User
from api.app.models.selections import LastPlayed, AutoPlay, Film, Episode
from api.app.models.content import Films, Shows, Seasons, Episodes
from api.app.models.events import ResumePaused


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
        last_played=values[7],
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
        file_key=values[4],
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
        file_key=values[4],
    )
    return previous_episode


def get_films() -> Films:
    query = "select film from films;"
    data = execute_query(query)
    values = sorted([x[0] for x in data])
    films = Films(films=values)
    return films


def get_film(film: str) -> Film:
    query = "select * from get_film_path(:film);"
    params = {"film": film}
    data = execute_query(query, params)
    values = data[0]
    selection = Film(
        film=film,
        file=values[0],
        file_key=values[3],
        plays=values[1],
        last_played=values[2],
    )
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
    query = "select * from get_show_path(:show, :season, :episode);"
    params = {"show": show, "season": season, "episode": episode}
    data = execute_query(query, params)
    values = data[0]
    selection = Episode(
        show=show,
        season=season,
        episode=episode,
        file=values[0],
        file_key=values[3],
        plays=values[1],
        last_played=values[2],
    )
    return selection


def get_paused_time(user_id: int) -> ResumePaused:
    query = "select video_progress from paused_content where user_id = :user_id order by play_num desc limit 1;"
    params = {"user_id": user_id}
    data = execute_query(query, params)
    if not data:
        value = 0.0
    else:
        value = data[0][0]
    return ResumePaused(seconds=value)
