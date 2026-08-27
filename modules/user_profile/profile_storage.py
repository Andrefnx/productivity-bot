import json
import os

from copy import deepcopy


# -------------------------------------------------------
#                   PROFILE STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

PROFILES_FILE = os.path.join(
    DATA_DIRECTORY,
    "profiles.json"
)

DEFAULT_PROFILE = {
    "xp": 0,
    "level": 1,
    "last_project_id": None,
    "imports": {},
    "economy": {
        "coins": 0,
        "lifetime_xp": 0,
        "lifetime_coins": 0,
        "sprints_rewarded": 0,
        "transactions": [],
        "migrations": {},
        "sprint_rewards": {}
    }
}


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

    changed = False

    if user_key not in profiles:
        profiles[user_key] = deepcopy(DEFAULT_PROFILE)
        changed = True

    profile = profiles[user_key]
    if "economy" not in profile:
        profile["economy"] = deepcopy(
            DEFAULT_PROFILE["economy"]
        )
        changed = True
    else:
        for key, value in DEFAULT_PROFILE["economy"].items():
            if key not in profile["economy"]:
                profile["economy"][key] = deepcopy(value)
                changed = True

    if changed:
        save_profiles(profiles)

    return profile


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
        deepcopy(DEFAULT_PROFILE)
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