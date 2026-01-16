import subprocess
import sys


def main() -> None:
    try:
        subprocess.run(["ruff", "format", "--check"], check=True)
    except subprocess.CalledProcessError:
        print("Formatting issues detected. Please format before merging")
        sys.exit(1)


if __name__ == "__main__":
    main()
