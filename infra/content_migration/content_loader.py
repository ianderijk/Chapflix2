import os
import subprocess
import time
from pathlib import Path

SOURCE_ROOT = Path("/media/idr/ExtDrive/Chapflix2/content")
TARGET_ROOT = Path("/media/ianderijk/Backup/Chapflix2/content")
KEY_PATH = Path("/home/idr/.ssh/id_rsa_target")
TARGET_ADDRESS = "ianderijk@192.168.0.29"


class Migration:
    def __init__(self) -> None:
        self.source_folders: list[Path] = [Path(x) for x in os.listdir(SOURCE_ROOT)]
        self.source_assets: list[Path] = self.get_source_assets()
        self.target_folders: list[Path] = self.get_target_folders()
        self.target_assets: list[Path] = self.get_target_assets()
        self.total_memory_migrating: int = 0
        self.file_memories: dict[Path, int] = {}
        self.time_elapsed: float = 0.0

    def get_source_assets(self) -> list[Path]:
        files = []
        for x in self.source_folders:
            if x == "images":
                continue
            files += [x / y for y in os.listdir(SOURCE_ROOT / x)]
        return files

    def list_dir_ssh(self, folder: Path = Path(), files: bool = False) -> list[str]:
        command = (
            f'find "{TARGET_ROOT}/{folder}" -maxdepth 1 -type f -printf "%f\n"'
            if files
            else f'find /{TARGET_ROOT} -maxdepth 1 -type d -printf "%f\n"'
        )
        return ["ssh", "-i", str(KEY_PATH), TARGET_ADDRESS, command]

    def get_target_folders(self) -> list[Path]:
        target_data = subprocess.run(
            self.list_dir_ssh(), capture_output=True, text=True
        )
        folder_names = target_data.stdout
        target_folder_names = [
            Path(x) for x in folder_names.split("\n") if x != "content"
        ]
        return target_folder_names

    def get_target_assets(self) -> list[Path]:
        files = []
        for x in self.target_folders:
            file_data = subprocess.run(
                self.list_dir_ssh(x, True),
                capture_output=True,
                text=True,
            )
            file_names = file_data.stdout.split("\n")
            files += [Path(x) / y for y in file_names]
        return files

    def find_folders_to_create(self) -> list[Path]:
        return [x for x in self.source_folders if x not in self.target_folders]

    def missing_folders_command(self, folder: Path) -> list[str]:
        return ["ssh", "-i", str(KEY_PATH), TARGET_ADDRESS, f"mkdir -p {folder}"]

    def create_missing_folders(self) -> None:
        missing_folders = self.find_folders_to_create()
        for x in missing_folders:
            path = TARGET_ROOT / x
            subprocess.run(self.missing_folders_command(path))

    def find_files_to_migrate(self) -> list[tuple[Path, Path]]:
        migration_assets = [
            x for x in self.source_assets if x not in self.target_assets
        ]
        migration_asset_pairs = [
            (SOURCE_ROOT / x, TARGET_ROOT / x) for x in migration_assets
        ]
        return migration_asset_pairs

    def calculate_migrating_memory(
        self, migration_pairs: list[tuple[Path, Path]]
    ) -> None:
        for x, _ in migration_pairs:
            filesize = os.path.getsize(x)
            self.file_memories[x] = filesize
        self.total_memory_migrating += sum(x for x in self.file_memories.values())

    def formatted_progress(self, progress: float) -> str:
        value = (progress / self.total_memory_migrating) * 100
        value_str = str(value)
        decimal_places = "".join([x for x in value_str.split(".")[-1]])
        if all(x == "0" for x in decimal_places):
            return str(int(value))
        return f"{value:.5f}"

    def calculate_remaining_time(
        self, start: float, end: float, cur_progress: str
    ) -> float:
        time_taken = end - start
        self.time_elapsed += time_taken
        progress = float(cur_progress)
        remaining_transfer = 100 - progress
        time_per_pct = self.time_elapsed / progress
        remaining_time = remaining_transfer * time_per_pct
        return remaining_time

    def format_remaining_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        seconds_ = int(seconds % 60)
        return f"{minutes}:{seconds_}"

    def migrate_files(self) -> None:
        files_to_migrate = self.find_files_to_migrate()
        self.calculate_migrating_memory(files_to_migrate)
        progress = 0
        for x, y in files_to_migrate:
            loop_start = time.time()
            print(f"Migrating: {x}")
            command = ["scp", "-i", KEY_PATH, x, f"{TARGET_ADDRESS}:{y}"]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                pass
            else:
                raise Exception(f"Failed to copy {x} to {y}")
            progress += self.file_memories[x]
            progress_value = self.formatted_progress(progress)
            print(f"Completion: {progress_value}%")
            loop_end = time.time()
            remaining_seconds = self.calculate_remaining_time(
                loop_start, loop_end, progress_value
            )
            remaining_time = self.format_remaining_time(remaining_seconds)
            print(f"ETA: {remaining_time}")

    def add_files_to_database(self) -> None:
        command = [
            "ssh",
            "-i",
            KEY_PATH,
            TARGET_ADDRESS,
            (
                "cd /media/ianderijk/Backup/Chapflix2/ &&"
                "source .venv/bin/activate &&"
                "python3 -m app.src.db_load incremental"
            ),
        ]
        subprocess.run(command)
        restart_system = [
            "ssh",
            "-i",
            KEY_PATH,
            TARGET_ADDRESS,
            "sudo systemctl restart chapflix.service",
        ]
        subprocess.run(restart_system)

    def main(self) -> None:
        self.create_missing_folders()
        self.migrate_files()
        self.add_files_to_database()


def main() -> None:
    migration = Migration()
    migration.main()


if __name__ == "__main__":
    main()
