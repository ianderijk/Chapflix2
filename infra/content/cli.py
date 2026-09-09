import typer

from .content_migrate import Migration
from .content_load import load_db

app = typer.Typer()


@app.command()
def push_content():
    Migration().main()
    load_db()


if __name__ == "__main__":
    app()
