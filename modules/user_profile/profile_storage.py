import json
import os


# -------------------------------------------------------
#                   PROFILE STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

PROFILES_FILE = os.path.join(
    DATA_DIRECTORY,
    "profiles.json"
)


def load_profiles():
    if not os.path.exists(
        PROFILES_FILE
    ):
        return {}

    try:
        with open(
            PROFILES_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):
        return {}


def save_profiles(
    profiles
):
    os.makedirs(
        DATA_DIRECTORY,
        exist_ok=True
    )

    with open(
        PROFILES_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            profiles,
            file,
            indent=4,
            ensure_ascii=False
        )


# -------------------------------------------------------
#                    PROFILE DATA
# -------------------------------------------------------

def get_profile(
    user_id: int
):
    profiles = load_profiles()

    user_key = str(
        user_id
    )

    if user_key not in profiles:
        profiles[user_key] = {
            "xp": 0,
            "level": 0,
            "last_project_id": None,
            "imports": {}
        }

        save_profiles(
            profiles
        )

    return profiles[
        user_key
    ]


def update_profile(
    user_id: int,
    data: dict
):
    profiles = load_profiles()

    user_key = str(
        user_id
    )

    profile = profiles.get(
        user_key,
        {
            "xp": 0,
            "level": 0,
            "last_project_id": None,
            "imports": {}
        }
    )

    profile.update(
        data
    )

    profiles[
        user_key
    ] = profile

    save_profiles(
        profiles
    )

    return profile


# -------------------------------------------------------
#                 LAST SPRINT PROJECT
# -------------------------------------------------------

def set_last_project(
    user_id: int,
    project_id,
    project_name=None
):
    profiles = load_profiles()

    user_key = str(
        user_id
    )

    profile = profiles.get(
        user_key,
        {
            "xp": 0,
            "level": 0,
            "last_project_id": None,
            "imports": {}
        }
    )

    profile[
        "last_project_id"
    ] = project_id

    profile.pop(
        "last_project_name",
        None
    )

    profiles[
        user_key
    ] = profile

    save_profiles(
        profiles
    )