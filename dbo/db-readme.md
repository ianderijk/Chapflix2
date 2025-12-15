# Database build requirements and steps

The database and its use within the app relies heavily on UDFs. During the course of development there are times when the result set of functions changes which means updates can't be made using a create or replace statement in the function's code. To ensure that functions always deliver the right results there is a shell script that drops all functions and recreates them. In order for the script to work there are some prerequisites.

1) A user profile needs to be set in the database (buildusr)
```
create role buildusr;
alter role buildusr with login password 'buildusr';
grant usage on schema public to buildusr;
grant create on schema public to buildusr;
grant all on all functions in schema public to buildusr;
```
2) Functions must be owned by the new user
```
alter function get_film_path(text) owner to buildusr;
alter function get_last_played() owner to buildusr;
alter function get_next_episode() owner to buildusr;
alter function get_previous_episode() owner to buildusr;
alter function get_show_path(text, integer, integer) owner to buildusr;
alter function get_show(text) owner to buildusr;
alter function incremental_load_content() owner to buildusr;
```
3) The user must be able to access the database and execute from shell scripts, to do this an update needs making to the postgres config file.
```
sudo -u postgres psql -c "SHOW hba_file;"
```
The command above will return the filepath of the hba_file. With the absolute path, open the file in nano. It's probably in 
```
/etc/postgresql/<version-number>/main
```
Add the following line to the end of the file, updating the device number based on it's static ip.
```
host    <database-name>    buildusr    127.0.0.1/<device-number>    trust
```
There will be a preceding line not far above in the file that looks something like the below. One or two fields might be different, change them to all, all and peer.
```
local   all     all         peer
```
4) Having made these changes, reload the postgres service
```
sudo systemctl reload postgresql
```
5) From this point the reset_functions shell script should run. It will require the buildusr password for each execution, this can be fixed later. Also, remember that the paths in the script are absolute paths which will differ so will need updating.