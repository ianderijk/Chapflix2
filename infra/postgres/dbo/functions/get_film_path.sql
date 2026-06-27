create or replace function get_film_path(film text)
returns table(
file text,
plays integer,
last_played timestamp
)
as
$$
with last_played as (
	select file_key
		,count(file_key) as plays
		,max(time) as last_played
	from history
	group by file_key
)
select c.file
	,lp.plays
	,lp.last_played
from films f
left join content c on f.file_key = c.file_key
left join last_played lp on f.file_key = lp.file_key
where f.film = get_film_path.film;
$$
language sql;
