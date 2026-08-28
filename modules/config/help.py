from modules.help.help_messages import (
    SETTINGS_DESCRIPTION,
    SETTINGS_TITLE
)


def register_help(registry):
    registry.register(
        key="settings",
        label="Settings",
        description="Privacy, timezone and preferences",
        order=40,
        renderer=lambda: (SETTINGS_TITLE, SETTINGS_DESCRIPTION)
    )