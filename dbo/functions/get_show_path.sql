-- 
-- Function: get_show_path
-- 
-- Description:
-- This function retrieves the file path for a specific show, season, and episode 
-- from the database. It performs a left join between the 'shows' and 'content' 
-- tables to find the corresponding file associated with the provided parameters.
-- 
-- Parameters:
--   show (text): The name of the show.
--   season (integer): The season number of the show.
--   episode (integer): The episode number of the show.
-- 
-- Returns:
--   A table containing the file path (text) for the specified show, season, and episode.
-- 
-- Usage:
-- Call this function with the appropriate show name, season number, and episode number 
-- to retrieve the corresponding file path.
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