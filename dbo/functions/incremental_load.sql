-- 
-- Function: incremental_load_content
-- 
-- Description:
-- This function retrieves a list of files from the 'content' table that do not have 
-- corresponding entries in the 'shows' or 'films' tables. It performs a left join 
-- on both tables using the 'file_key' to identify files that are not associated 
-- with any shows or films.
-- 
-- Returns:
-- A table containing a single column 'file' of type text, which lists the files 
-- that are not linked to any shows or films.
-- 
-- Usage:
-- Call this function to perform an incremental load of content files that are 
-- not yet associated with any shows or films.
-- 
-- Example:
-- SELECT * FROM incremental_load_content();
-- 
-- Filepath:
-- /media/idr/ExtDrive/Chapflix/dbo/functions/incremental_load.sql
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
