create or replace function incremental_load_content()
returns table(
file text
)
as
$$
select c.file
from content c
left join shows s on c.file_key = s.file_key
left join films f on c.file_key = f.file_key
where coalesce(s.show, f.film) is null;
$$
language sql;
