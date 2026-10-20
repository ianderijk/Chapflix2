CREATE OR REPLACE FUNCTION GET_LAST_PLAYED (USR_ID INTEGER) RETURNS TABLE (
	MEDIA_TYPE TEXT,
	FILE_KEY INTEGER,
	FILM TEXT,
	SHOW TEXT,
	SEASON INTEGER,
	EPISODE INTEGER,
	FILE TEXT,
	LAST_PLAYED TIMESTAMP,
	DURATION INTEGER
) AS $$
select case when f.film is not null then 'film' else 'show' end as media_type
	,coalesce(f.file_key, s.file_key) as file_key
	,f.film
	,s.show
	,s.season
	,s.episode
	,c.file
	,h.time as last_played
	,case when f.film is not null then f.duration else s.duration end as duration
from history h
left join shows s on h.file_key = s.file_key
left join films f on h.file_key = f.file_key
left join content c on h.file_key = c.file_key
where h.user_id = usr_id
order by time desc
limit 1
$$ LANGUAGE SQL;
