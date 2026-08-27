from .user.user_config import get_user_config


# -------------------------------------------------------
#                  PROFILE VISIBILITY
# -------------------------------------------------------

def can_view_profile(
    owner,
    viewer,
    guild=None
):
    if owner.id == viewer.id:
        return True

    config = get_user_config(
        owner.id
    )

    return config[
        "profile_visibility"
    ] == "public"


# -------------------------------------------------------
#                 PROJECT VISIBILITY
# -------------------------------------------------------

def can_view_projects(
    owner,
    viewer,
    guild=None
):
    if owner.id == viewer.id:
        return True

    config = get_user_config(
        owner.id
    )

    return config[
        "projects_visibility"
    ] == "public"


__all__ = [
    "can_view_profile",
    "can_view_projects"
]