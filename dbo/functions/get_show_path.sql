create or replace function get_show_path(show_ text, season integer, episode integer)
returns table (
file text
)
as 
$$
select c.file
from shows s
left join content c on s.file_key = c.file_key
where s.show = get_show_path.show_
	and s.season = get_show_path.season
	and s.episode = get_show_path.episode;
$$
language sql;