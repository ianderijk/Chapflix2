create or replace procedure create_schema_tables()
language plpgsql
as
$$
begin
	create table if not exists content (
		file_key serial primary key,
		file text not null
	);

	create table if not exists films (
		file_key integer primary key,
		film text,
		duration numeric,
		foreign key (file_key) references content(file_key)
	);

	create table if not exists shows (
		file_key integer primary key,
		show text,
		season integer,
		episode integer,
		duration numeric,
		foreign key (file_key) references content(file_key)
	);

	create table if not exists history (
		play_num serial primary key,
		file_key integer,
		time timestamp,
		user_id integer,
		foreign key (file_key) references content(file_key)
	);

	create table if not exists users (
		user_id serial primary key,
		display_name text
	);

	create table if not exists paused_content (
		play_num serial,
		user_id integer,
		file_key integer,
		video_progress decimal
	);
end;
$$;
