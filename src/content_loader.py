from __future__ import annotations
import os
import subprocess

SOURCE_ROOT = os.path.join("/media", "idr", "ExtDrive", "Chapflix2", "assets")
TARGET_ROOT = os.path.join("/media", "ianderijk", "Backup", "Chapflix2", "assets")
KEY_PATH = os.path.join("/home", "idr", ".ssh", "id_rsa_target")
TARGET_ADDRESS = "ianderijk@192.168.0.29"


class Migration:
    def __init__(self) -> None:
        self.source_folders = os.listdir(SOURCE_ROOT)
        self.source_assets = self.get_source_assets()
        self.target_folders = self.get_target_folders()
        self.target_assets = self.get_target_assets()

    def get_source_assets(self) -> list:
        files = []
        for x in self.source_folders:
            if x == "images":
                continue
            files += [
                os.path.join(x, y) for y in os.listdir(os.path.join(SOURCE_ROOT, x))
            ]
        return files

    def clean_target_data(self, stdout: str, files: bool) -> list:
        assets_text = stdout.replace("total 100", "")
        if files:
            assets_data = assets_text.split("-rw-rw-r--")
            tail_names = [x.split(" ")[-1].replace("\n", "") for x in assets_data][1:]
            return [x for x in tail_names if x != "images"]

        assets_data = assets_text.split("drwxr-xr-x")
        tail_names = [x.split(" ")[-1].replace("\n", "") for x in assets_data][1:]
        return [x for x in tail_names if x != "images"]

    def list_dir_ssh(self, folder: str = "") -> list:
        return [
            "ssh",
            "-i",
            KEY_PATH,
            TARGET_ADDRESS,
            f"ls -l {TARGET_ROOT}/{folder}",
        ]

    def get_target_folders(self) -> list:
        target_data = subprocess.run(
            self.list_dir_ssh(), capture_output=True, text=True
        )
        target_folder_names = self.clean_target_data(target_data.stdout, False)
        return target_folder_names

    def get_target_assets(self) -> list:
        files = []
        for x in self.target_folders:
            file_data = subprocess.run(
                self.list_dir_ssh(x),
                capture_output=True,
                text=True,
            )
            file_names = self.clean_target_data(file_data.stdout, True)
            files += [f"{x}/{y}" for y in file_names]
        return files

    def find_folders_to_create(self) -> list:
        return [x for x in self.source_folders if x not in self.target_folders]

    def create_missing_folders(self) -> None:
        missing_folders = self.find_folders_to_create()
        command = lambda x: ["ssh", "-i", KEY_PATH, TARGET_ADDRESS, f"mkdir -p {x}"]
        for x in missing_folders:
            path = os.path.join(TARGET_ROOT, x)
            subprocess.run(command(path))

    def find_files_to_migrate(self) -> list[tuple[str, str]]:
        migration_assets = [
            x for x in self.source_assets if x not in self.target_assets
        ]
        migration_asset_pairs = [
            (os.path.join(SOURCE_ROOT, x), os.path.join(TARGET_ROOT, x))
            for x in migration_assets
        ]
        return migration_asset_pairs

    def migrate_files(self) -> None:
        files_to_migrate = self.find_files_to_migrate()
        for x, y in files_to_migrate:
            command = ["scp", "-i", KEY_PATH, x, f"{TARGET_ADDRESS}:{y}"]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                pass
            else:
                raise Exception(f"Failed to copy {x} to {y}")

    def add_files_to_database(self) -> None:
        command = [
            "ssh",
            "-i",
            KEY_PATH,
            TARGET_ADDRESS,
            "cd /media/ianderijk/Backup/Chapflix2/ && /media/ianderijk/Backup/Chapflix2/.venv/bin/python3 -m src.dbconn",
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
