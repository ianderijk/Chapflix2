-- 
-- Function: get_show
-- 
-- Description:
-- This function retrieves the most recent episode of a specified show from the history.
-- It returns a table containing the show name, season number, and episode number.
-- 
-- Parameters:
--   selection (text): The name of the show for which the most recent episode is to be retrieved.
-- 
-- Returns:
--   A table with the following columns:
--     - show (text): The name of the show.
--     - season (integer): The season number of the episode.
--     - episode (integer): The episode number of the episode.
-- 
-- Usage:
-- Call this function with the name of the show to get the latest episode details.
-- 
-- Example:
-- SELECT * FROM get_show('Some Show Name');
-- 
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