# Chapflix
Chapflix is a simple and lightweight web-app desgined to allow for the serving of media content. No tracking, no ads and no subscription, just content and privacy.


## How to use
Activate the venv and run the main file!
>
source .venv/bin/activate
uv run main.py
>

### Adding new content
Convert new content from discs and add it to the assets folder as per existing naming conventions then run the dbconn file with incremental_load function to add the content to the database. Disconnect the external drive from the raspberry pi and connect it to the pc then run the incremental copy program written in go (see ChapflixLoad repo). Reconnect the external drive to the pi and run dbconn module on the pi. Ensure the service for running the app has been resumed on the pi.


## Contents
The project consists of a main file, a src folder, a tests folder, an assets folder and a postgres database connection. 

The main file contains all code relating the front end of the web-app which is built using the Dash library.

The player module contains code that acts as an intermediary between the data required for the app to run and the data stored in the database. A single class (Player) loads all required data upon initialisation and contains methods that take input data from selections in the app and return required data from the database.

The dbconn module contains functions to interact with the database. Within this module are functions required for use in the app as well as functions that combine to create an initial build routine and an incremental load routine. Both load routines can be executed by calling the dedicated function for each routine.

The database is a local postgres instance. The data model is simple, only 4 tables in total. The content table is the central table which contains a record of every media file available for serving. Each file is assigned a unique key. This key is then used as a foreign key in the three other tables which consist of a table for films, one for shows and the final table recording played media.

There is also a dbo folder within the project which is used to keep a record of the code required to create all function and stored procedures.


## Further development
Current priority is to add more content to the library.
Productionising and serving as an always-on application on the pi.
Above would ideally include a CI/CD pipeline and docker containerisation.
Adding in a play from previous selection button.
Adding images and audio files to make selections more fun.
