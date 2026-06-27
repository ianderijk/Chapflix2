create or replace function get_file_mappings()
returns table (
filename text,
file text
)
as
$$
select coalesce(f.film, concat(s.show, s.season, s.episode)) as filename
	,c.file
from content c
left join shows s on c.file_key = s.file_key
left join films f on c.file_key = f.file_key;
$$
language sql;
