create or replace function get_next_episode(usr_id integer)
returns table (
file text,
show text,
season integer,
episode integer,
file_key integer
)
as
$$
with last_played as (
	select *
	from get_last_played(usr_id)
)
,max_episode_in_season as (
	select show
		,season
		,max(episode) as max_episode
	from shows
	where show = (select show from last_played)
		and season = (select season from last_played)
	group by show, season
)
,last_played_versus_season as (
	select lp.*
		,meis.max_episode
	from last_played as lp
	left join max_episode_in_season as meis on lp.show = meis.show
)
,same_season as (
	select s.show
		,s.season
		,s.episode
		,c.file
	from shows as s
	left join content as c on s.file_key = c.file_key
	where s.show = (select show from last_played)
		and s.season = (select season from last_played)
		and s.episode = (select episode from last_played) + 1
)
,next_season as (
	select *
	from (
		select *, row_number() over(partition by show order by episode) as wf
		from shows
		where show = (select show from last_played)
			and season = (select season from last_played) + 1
		) as sq
	where sq.wf = 1
)
select case when lpvs.episode != lpvs.max_episode then ss.file
			when ns.show is not null then c.file
			else null end as next_episode_path
		,case when lpvs.episode != lpvs.max_episode then ss.show
			when ns.show is not null then ns.show
			else null end as next_show
		,case when lpvs.episode != lpvs.max_episode then ss.season
			when ns.show is not null then ns.season
			else null end as next_season
		,case when lpvs.episode != lpvs.max_episode then ss.episode
			when ns.show is not null then ns.episode
			else null end as next_episode
        ,case when lpvs.episode != lpvs.max_episode then c.file_key
            when ns.show is not null then c.file_key
            else null end as file_key
from last_played_versus_season as lpvs
left join same_season as ss on lpvs.show = ss.show
left join next_season as ns on lpvs.show = ns.show
left join content as c on ns.file_key = c.file_key
$$
language sql;
