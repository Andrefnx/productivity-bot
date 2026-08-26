from modules.user_profile.profile_storage import (
    load_profiles,
    save_profiles
)


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
    profiles = load_profiles()

    user_key = str(
        user_id
    )

    profile = profiles.get(
        user_key,
        {}
    )

    saved_config = profile.get(
        "config",
        {}
    )

    config = DEFAULT_CONFIG.copy()

    config.update(
        saved_config
    )

    return config


def update_user_config(
    user_id: int,
    key: str,
    value
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

    config = DEFAULT_CONFIG.copy()

    config.update(
        profile.get(
            "config",
            {}
        )
    )

    config[
        key
    ] = value

    profile[
        "config"
    ] = config

    profiles[
        user_key
    ] = profile

    save_profiles(
        profiles
    )

    return config