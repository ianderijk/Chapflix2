import argparse
from .dbconn import initial_build, incremental_build


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["initial", "incremental"])
    args = parser.parse_args()

    if args.mode == "initial":
        initial_build()
    else:
        incremental_build()


if __name__ == "__main__":
    main()
