
create or replace function get_last_played(usr_id integer)
returns table(
media_type text,
file_key integer,
film text,
show text,
season integer,
episode integer,
file text
)
as
$$
select case when f.film is not null then 'film' else 'show' end as media_type
	,coalesce(f.file_key, s.file_key) as file_key
	,f.film
	,s.show
	,s.season
	,s.episode
	,c.file
from history h
left join shows s on h.file_key = s.file_key
left join films f on h.file_key = f.file_key
left join content c on h.file_key = c.file_key
where h.user_id = usr_id
order by time desc
limit 1
$$
language sql;
