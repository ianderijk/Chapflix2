import typer

from infra.content.content_migrate import Migration
from infra.content.content_load import load_db

app = typer.Typer()


@app.command()
def load_content():
    load_db()


@app.command()
def push_content():
    Migration().main()


if __name__ == "__main__":
    app()
