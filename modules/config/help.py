SETTINGS_TITLE = "Settings"

SETTINGS_DESCRIPTION = (
    "Use `/config` to manage your preferences and server configuration.\n\n"
    "**User Settings**\n"
    "Manage your personal privacy, timezone, and time format preferences.\n\n"
    "**Channel Settings**\n"
    "Configure sprint permissions, behavior, timing, and empty sprint handling "
    "for this server."
)


def register_help(registry):
    registry.register(
        key="settings",
        label="Settings",
        description="Privacy, timezone and preferences",
        order=40,
        renderer=lambda: (SETTINGS_TITLE, SETTINGS_DESCRIPTION)
    )
