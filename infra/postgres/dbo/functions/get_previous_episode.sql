/*
Function: get_previous_episode()

Purpose:
Retrieves the previous episode for a show based on the last played episode.
If the current episode is the first in the season, returns the last episode 
of the previous season. Returns NULL if no previous episode exists.

Returns:
- file (text): File path of the previous episode
- show (text): Show name of the previous episode
- season (integer): Season number of the previous episode
- episode (integer): Episode number of the previous episode

Logic Flow:
1. Identifies the last played episode from get_last_played()
2. Finds the minimum episode number in the current season
3. Determines if the last played episode is the first in the season
4. If not first: returns the previous episode in the same season
5. If first: returns the last episode from the previous season
6. Returns NULL values if no previous episode exists

Dependencies:
- get_last_played(): Function that returns the currently last played episode
- shows: Table containing episode metadata
- content: Table containing file information linked via file_key

Author: [Unknown]
Created: [Unknown]
Last Modified: [Unknown]
*/
create or replace function get_previous_episode(usr_id integer)
returns table (
file text,
show text,
season integer,
episode integer
)
as
$$
with last_played as (
	select *
	from get_last_played(usr_id)
)
,min_episode_in_season as (
	select show
		,season
		,min(episode) as min_episode
	from shows
	where show = (select show from last_played)
		and season = (select season from last_played)
	group by show, season
)
,last_played_versus_season as (
	select lp.*
		,meis.min_episode
	from last_played as lp
	left join min_episode_in_season as meis on lp.show = meis.show
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
		and s.episode = (select episode from last_played) - 1
)
,previous_season as (
	select *
	from (
		select *, row_number() over(partition by show order by episode desc) as wf
		from shows
		where show = (select show from last_played)
			and season = (select season from last_played) - 1
		) as sq
	where sq.wf = 1
)
select case when lpvs.episode != lpvs.min_episode then ss.file
			when ps.show is not null then c.file
			else null end as next_episode_path
		,case when lpvs.episode != lpvs.min_episode then ss.show
			when ps.show is not null then ps.show
			else null end as next_show
		,case when lpvs.episode != lpvs.min_episode then ss.season
			when ps.show is not null then ps.season
			else null end as next_season
		,case when lpvs.episode != lpvs.min_episode then ss.episode
			when ps.show is not null then ps.episode
			else null end as next_episode
from last_played_versus_season as lpvs
left join same_season as ss on lpvs.show = ss.show
left join previous_season as ps on lpvs.show = ps.show
left join content as c on ps.file_key = c.file_key
$$
language sql;