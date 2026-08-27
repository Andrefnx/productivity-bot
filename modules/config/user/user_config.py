# -------------------------------------------------------
#                    CONFIG DEFAULTS
# -------------------------------------------------------

DEFAULT_CONFIG = {
    "profile_visibility": "private",
    "projects_visibility": "private",
    "time_format": "12h",
    "timezone": "America/Punta_Arenas"
}


# -------------------------------------------------------
#                     CONFIG DATA
# -------------------------------------------------------

def get_user_config(
    user_id: int
):
    from modules.user_profile.profile_storage import load_profiles

    profiles = load_profiles()

    profile = profiles.get(
        str(user_id),
        {}
    )

    config = DEFAULT_CONFIG.copy()
    config.update(
        profile.get(
            "config",
            {}
        )
    )

    return config


def update_user_config(
    user_id: int,
    key: str,
    value
):
    if key not in DEFAULT_CONFIG:
        raise KeyError(
            f"Unknown user config key: {key}"
        )

    if key in (
        "profile_visibility",
        "projects_visibility"
    ) and value not in (
        "public",
        "private"
    ):
        raise ValueError(
            f"Invalid value for {key}: {value}"
        )

    if key == "time_format" and value not in (
        "12h",
        "24h"
    ):
        raise ValueError(
            f"Invalid value for {key}: {value}"
        )

    from modules.user_profile.profile_storage import (
        load_profiles,
        save_profiles
    )

    profiles = load_profiles()
    user_key = str(user_id)
    profile = profiles.get(
        user_key,
        {
            "xp": 0,
            "level": 0,
            "last_project_id": None,
            "imports": {}
        }
    )

    config = get_user_config(
        user_id
    )
    config[key] = value
    profile["config"] = config
    profiles[user_key] = profile

    save_profiles(
        profiles
    )

    return config


__all__ = [
    "DEFAULT_CONFIG",
    "get_user_config",
    "update_user_config"
]