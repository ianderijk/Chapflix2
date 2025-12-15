create or replace function get_show(selection text)
returns table (
	show text,
	season integer,
	episode integer
)
as
$$
select s.show
	,s.season
	,s.episode
from history h
left join shows s on h.file_key = s.file_key
where s.show = selection
order by h.time desc
limit 1
$$
language sql;