from modules.common.entitlements import FEATURE_BOT_CUSTOMIZATION


BOT_PROFILE_CUSTOMIZATION_TITLE = "Bot Profile Customization"

BOT_PROFILE_CUSTOMIZATION_DESCRIPTION = (
    "Use `/config` and select **Bot Appearance** to customize "
    "how the bot appears.\n\n"
    "**Server bot name**\n"
    "Change the bot nickname for this server.\n\n"
    "**Reset bot name**\n"
    "Restore the bot's default/global name in this server.\n\n"
    "**Global bot avatar**\n"
    "Change the bot avatar across all servers. Only available "
    "to the configured bot owner."
)


def register_help(registry):
    registry.register(
        key="bot_profile_customization",
        label="Bot Profile Customization",
        description="Customize the bot name and profile",
        order=50,
        renderer=lambda: (
            BOT_PROFILE_CUSTOMIZATION_TITLE,
            BOT_PROFILE_CUSTOMIZATION_DESCRIPTION
        ),
        requires_feature=FEATURE_BOT_CUSTOMIZATION
    )