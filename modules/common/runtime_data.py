import json
from pathlib import Path


RUNTIME_DATA_DEFAULTS = {
    "active_sprints.json": [],
    "channel_config.json": {},
    "profiles.json": {},
    "projects.json": {},
    "sprint_users.json": {}
}


def ensure_runtime_data_files(data_directory="data"):
    directory = Path(data_directory)
    directory.mkdir(parents=True, exist_ok=True)

    for filename, default_value in RUNTIME_DATA_DEFAULTS.items():
        file_path = directory / filename

        if file_path.exists():
            continue

        with file_path.open("w", encoding="utf-8") as data_file:
            json.dump(default_value, data_file, indent=4)