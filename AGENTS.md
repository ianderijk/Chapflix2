# Project Overview

Chapflix is a self-hosted, custom streaming service designed to facilitate watching a relavtively small number of classic shows and films. The project consists of a postgres database, the media files (stored under the content/ directory), a package to load data into the database and migrate the media files to the production server, a database utilites package, a FastAPI instance making the required data available and the web-app. The api and app are built into their own docker containers and the postgres instance also resides in a container.

## Agent Role

The agent in this project is the frontend developer. The creator of the project handles the database ingestion and management, file migration and api development as well as all infrastructure related tasks. The agent may only work within the app/ and assets/ directories of the repo and under no circumstances is allowed to make changes to any file outside of those two directories. 

## Coding standards

The backend is all written using python, sql and shell scripts. Any code written in python must adhere to `ruff` formatting and linting rules and `ty` typechecking. These standards are enforced by both the pre-commit hook and CI workflow. Where the agent writes using other languages (eg javascript, css etc.) formatting and linting is considered mandatory. If there are insufficient tools then permission must be asked before installing anything.
Do not litter the code with comments, code that requires extensive inline prose to explain what it does is poorly written and should be broken down into helper functions. Where code is genuinely complex and required, prefer docstrings to comments and create or edit README.md files specific to the area of the project being worked on.
Do not assume the functionality of code based on variable and function names, always review the code to gain insight into its functionality.
Review backend code as part of writing frontend code that integrates effectively with the backend. If an api endpoint raises an exception instead of returning malformed data there is no need to write checks for bad data in frontend code. Where data contracts are lacking clarity or judgement is that improvements may be made to the backend, suggest them.

## Collaboration

While the creator is not permitting changes be made to the backend code it is acceptable to request features to support frontend development. New api endpoints, new database functions and fields are within scope for active development of the frontend.
