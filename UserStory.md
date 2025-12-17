# Story: Video timer
As a user I would like to have the app record the timestamp of the video when I pause it so that I can resume watching the same content from the same timestamp on my next session.

# Tasks
## Implement video timer capture
Need to write new callbacks, js functions and dash elements to collect the timestamp data on pausing the video.

## User selection functionality
Add in a dropdown box where the user picks who is watching. Set the other functionality to be dependent on this field being populated before serving any content.

## Make last watched message dependent on user
Don't populate the continue watching message until the user has been selected then when it is, update the message based on the user.
Make the next, previous and continue buttons all user dependent

## Database updates
- Need to add in a users table to differentiate who was last watching and select the right content based on their last watch.
- Add a paused content table so that pause events can be recorded. Ensure that this table can join back to the corresponding record from the history table.



## Pi steps
- add in users table and insert data
```
create table if not exists users (
		user_id serial primary key,
		display_name text
	);
insert into users (display_name) values ('Lady'), ('Chap');
```

- add user_id column to history
```
alter table history
add column user_id integer;
```
- add paused_content table
```
create table if not exists paused_content (
		play_num integer,
		user_id integer,
		video_progress interval
	);
```
- function get_last_played() has changed, need to drop it and recreate
- both next and previous episode sql functions have changed so need dropping and recreating. probably best to just run the reset functions script now.