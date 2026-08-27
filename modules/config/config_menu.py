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


# -------------------------------------------------------
#                  CONFIGURATION MENU
# -------------------------------------------------------

class ConfigMenuView(
    discord.ui.View
):
    def __init__(
        self,
        owner
    ):
        super().__init__(
            timeout=180
        )
        self.owner = owner

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

    @discord.ui.button(
        label="User Settings",
        style=discord.ButtonStyle.primary
    )
    async def user_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            embed=create_config_embed(
                self.owner
            ),
            view=ConfigView(
                owner=self.owner
            )
        )

    @discord.ui.button(
        label="Channel Settings",
        style=discord.ButtonStyle.secondary
    )
    async def channel_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not can_edit_channel_config(
            interaction.user
        ):
            await interaction.response.send_message(
                "Administrator or Manage Guild permission required.",
                ephemeral=True
            )
            return

        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message(
                "Channel settings are only available in a server channel.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            embed=create_channel_config_embed(
                interaction.guild.id,
                interaction.channel.id
            ),
            view=ChannelConfigView(
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id
            )
        )
