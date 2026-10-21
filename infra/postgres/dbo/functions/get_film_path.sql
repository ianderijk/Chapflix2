CREATE OR REPLACE FUNCTION GET_FILM_PATH (FILM TEXT) RETURNS TABLE (
	FILE TEXT,
	PLAYS INTEGER,
	LAST_PLAYED TIMESTAMP,
	FILE_KEY INTEGER,
	DURATION INTEGER
) AS $$
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
	,c.file_key
	,f.duration
from films f
left join content c on f.file_key = c.file_key
left join last_played lp on f.file_key = lp.file_key
where f.film = get_film_path.film;
$$ LANGUAGE SQL;
