import discord

from ..permissions import can_edit_channel_config
from .channel_views import ChannelConfigView, create_channel_config_embed


async def render_settings(interaction, owner):
    if not can_edit_channel_config(interaction.user):
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


def register_settings(registry):
    registry.register(
        key="channel_settings",
        label="Channel Settings",
        description="Permissions and sprint behavior",
        order=20,
        renderer=render_settings
    )