/**
 * get_last_played()
 * 
 * Description:
 *   Retrieves the most recently played media item from the viewing history.
 *   Returns details about either a film or show episode, including associated file information.
 * 
 * Returns:
 *   Table with the following columns:
 *   - media_type (text): Type of media - either 'film' or 'show'
 *   - file_key (integer): Unique identifier for the media file
 *   - film (text): Film title if media_type is 'film', NULL otherwise
 *   - show (text): Show title if media_type is 'show', NULL otherwise
 *   - season (integer): Season number if media_type is 'show', NULL otherwise
 *   - episode (integer): Episode number if media_type is 'show', NULL otherwise
 *   - file (text): File path or name of the media content
 * 
 * Example:
 *   SELECT * FROM get_last_played();
 * 
 * Notes:
 *   - Returns only the single most recently viewed item (LIMIT 1)
 *   - Results are ordered by history timestamp in descending order
 *   - Uses LEFT JOINs to accommodate both film and show media types
 */
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