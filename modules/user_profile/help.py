from modules.help.help_messages import (
    PROFILE_DESCRIPTION,
    PROFILE_TITLE
)


def register_help(registry):
    registry.register(
        key="profile",
        label="Profile",
        description="Your personal bot menu",
        order=30,
        renderer=lambda: (PROFILE_TITLE, PROFILE_DESCRIPTION)
    )