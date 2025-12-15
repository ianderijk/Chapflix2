create or replace function get_film_path(film text)
returns table(
file text
)
as
$$
select c.file
from films f
left join content c on f.file_key = c.file_key
where f.film = get_film_path.film;
$$
language sql;