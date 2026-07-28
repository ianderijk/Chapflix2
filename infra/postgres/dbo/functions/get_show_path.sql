create or replace function get_show_path(show_ text, season integer, episode integer)
returns table (
file text,
plays integer,
last_played timestamp,
file_key integer
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
    ,c.file_key
from shows s
left join content c on s.file_key = c.file_key
left join last_played lp on s.file_key = lp.file_key
where s.show = get_show_path.show_
	and s.season = get_show_path.season
	and s.episode = get_show_path.episode;
$$
language sql;
