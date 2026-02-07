/**
 * @function get_film_path
 * @description Retrieves the file path(s) associated with a given film title.
 *              Performs a left join between the films and content tables to match
 *              films by their file_key and returns the corresponding file paths.
 * 
 * @param film (text) - The film title to search for
 * 
 * @returns table(file text) - A table containing the file path(s) for the specified film.
 *                             Returns NULL if no matching content is found.
 * 
 * @example
 *   SELECT * FROM get_film_path('Inception');
 * 
 * @note Uses a LEFT JOIN, which means films without associated content will return
 *       NULL for the file column. Consider using INNER JOIN if only films with
 *       existing files should be returned.
 */
create or replace function get_film_path(film text)
returns table(
file text
)
as
$$
select c.file
from films f
left join content c on f.file_key = c.file_key
where f.film = get_film_path.film;
$$
language sql;