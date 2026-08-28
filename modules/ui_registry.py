from modules.common.ui.registry import UIRegistry


def get_help_registry():
    registry = UIRegistry("help")

    from modules.help.help_entries import register_help
    from modules.sprints.help import register_help as register_sprint_help
    from modules.user_profile.projects.help import (
        register_help as register_project_help
    )
    from modules.user_profile.help import register_help as register_profile_help
    from modules.config.help import register_help as register_config_help
    from modules.bot_appearance.help import register_help as register_appearance_help
    from modules.user_profile.imports.help import register_help as register_import_help

    for register in (
        register_help,
        register_sprint_help,
        register_project_help,
        register_profile_help,
        register_config_help,
        register_appearance_help,
        register_import_help
    ):
        register(registry)

    return registry


def get_settings_registry():
    registry = UIRegistry("settings")

    from modules.config.user.settings import register_settings as register_user_settings
    from modules.config.channel.settings import (
        register_settings as register_channel_settings
    )
    from modules.bot_appearance.settings import (
        register_settings as register_appearance_settings
    )

    for register in (
        register_user_settings,
        register_channel_settings,
        register_appearance_settings
    ):
        register(registry)

    return registry