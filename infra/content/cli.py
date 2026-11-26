import typer
import os
from dotenv import load_dotenv
from pathlib import Path

from infra.content.content_migrate import Migration
from infra.content.content_load import load_db, set_media_files
from utils.dbutils import create_db_engine

load_dotenv()

app = typer.Typer()

set_media_files(Path(os.getenv("MEDIA_FILES", Path())))
create_db_engine()


@app.command()
def load_content():
    load_db()


@app.command()
def push_content():
    Migration()


if __name__ == "__main__":
    app()
