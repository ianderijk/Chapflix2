from infra.content.content_load import load_db


def main() -> None:
    print("Loading content to database")
    load_db()
    print("Database loaded")


if __name__ == "__main__":
    main()
