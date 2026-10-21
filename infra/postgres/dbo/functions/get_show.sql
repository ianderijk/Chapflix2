CREATE OR REPLACE FUNCTION GET_SHOW (SELECTION TEXT) RETURNS TABLE (
	SHOW TEXT,
	SEASON INTEGER,
	EPISODE INTEGER,
	DURATION INTEGER
) AS $$
select s.show
	,s.season
	,s.episode
	,s.duration
from history h
left join shows s on h.file_key = s.file_key
where s.show = selection
order by h.time desc
limit 1
$$ LANGUAGE SQL;
