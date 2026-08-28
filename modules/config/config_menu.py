import discord

from .channel.channel_views import (
    ChannelConfigView,
    create_channel_config_embed
)

from .config_views import (
    ConfigView,
    create_config_embed
)

from .permissions import can_edit_channel_config
from modules.ui_registry import get_settings_registry


# -------------------------------------------------------
#                  CONFIGURATION MENU
# -------------------------------------------------------

class ConfigMenuView(
    discord.ui.View
):
    def __init__(
        self,
        owner,
        guild_id=None
    ):
        super().__init__(
            timeout=180
        )
        self.owner = owner
        self.guild_id = guild_id

        registry = get_settings_registry()
        self.add_item(
            SettingsSelect(
                registry=registry,
                owner=owner,
                guild_id=guild_id
            )
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "These settings belong to another user.",
                ephemeral=True
            )
            return False

        return True

class SettingsSelect(
    discord.ui.Select
):
    def __init__(
        self,
        registry,
        owner,
        guild_id
    ):
        self.registry = registry
        self.owner = owner
        self.guild_id = guild_id

        super().__init__(
            placeholder="Select a settings category",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=entry.label,
                    value=entry.key,
                    description=entry.description
                )
                for entry in registry.entries(guild_id=guild_id)
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        entry = self.registry.get(self.values[0])
        if entry not in self.registry.entries(
            guild_id=interaction.guild_id
        ):
            await interaction.response.send_message(
                "Settings section not found.",
                ephemeral=True
            )
            return

        await entry.renderer(
            interaction,
            self.owner
        )
