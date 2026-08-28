from dotenv import load_dotenv

import os

import discord

from discord import app_commands

from modules.sprints import (
    SprintCreateModal,
    recover_interrupted_sprints
)

from modules.user_profile import (
    ProfileView,
    create_profile_embed
)
from modules.config import (
    ConfigMenuView,
    can_create_sprint,
    get_channel_config
)

from modules.help import (
    HelpView,
    create_help_embed
)
#-------------------------------------------------------
#                       SETUP  
#-------------------------------------------------------


load_dotenv()

token = os.getenv("DISCORD_TOKEN")

if token is None:
    raise RuntimeError(
        "DISCORD_TOKEN was not found in the environment."
    )


intents = discord.Intents.default()

client = discord.Client(
    intents=intents
)

tree = app_commands.CommandTree(
    client
)

startup_recovery_done = False


# -------------------------------------------------------
#                       COMMANDS
# -------------------------------------------------------

# -------------------------------------------------------
#                       SPRINT
# -------------------------------------------------------

@tree.command(
    name="sprint",
    description="Start a writing sprint"
)
async def sprint(
    interaction: discord.Interaction
):
    channel_config = get_channel_config(
        interaction.guild_id,
        interaction.channel_id
    )

    if not can_create_sprint(
        interaction.user,
        channel_config["create_sprints"]
    ):
        await interaction.response.send_message(
            "You do not have permission to create sprints in this channel.",
            ephemeral=True
        )
        return

    sprint_modal = SprintCreateModal(
        default_duration=channel_config["default_duration"],
        default_start_waiting_time=channel_config["start_waiting_time"]
    )

    await interaction.response.send_modal(
        sprint_modal
    )

# -------------------------------------------------------
#                      PROFILE
# -------------------------------------------------------

@tree.command(
    name="profile",
    description="Open your profile"
)
async def profile(
    interaction: discord.Interaction
):
    await interaction.response.defer(
        ephemeral=True
    )

    profile_embed = create_profile_embed(
        interaction.user
    )

    profile_view = ProfileView(
        owner=interaction.user
    )

    await interaction.followup.send(
        embed=profile_embed,
        view=profile_view,
        ephemeral=True
    )
# -------------------------------------------------------
#                       CONFIG
# -------------------------------------------------------

@tree.command(
    name="config",
    description="Manage your settings"
)
async def config(
    interaction: discord.Interaction
):
    await interaction.response.defer(
        ephemeral=True
    )

    await interaction.followup.send(
        embed=discord.Embed(
            title="Settings",
            description="Choose a settings category."
        ),
        view=ConfigMenuView(
            owner=interaction.user,
            guild_id=interaction.guild_id
        ),
        ephemeral=True
    )

# -------------------------------------------------------
#                        HELP
# -------------------------------------------------------

@tree.command(
    name="help",
    description="Learn how to use the bot"
)
async def help_command(
    interaction: discord.Interaction
):
    await interaction.response.send_message(
        embed=create_help_embed(),
        view=HelpView(
            owner=interaction.user,
            guild_id=interaction.guild_id
        ),
        ephemeral=True
    )
# -------------------------------------------------------
#                  DISCORD CONNECTION
# -------------------------------------------------------

@client.event
async def on_ready():
    global startup_recovery_done

    if not startup_recovery_done:
        await recover_interrupted_sprints(
            client
        )

        startup_recovery_done = True

    synced = await tree.sync()

    print(
        f"Synced commands: {len(synced)}"
    )

    print(
        f"Logged in as: {client.user}"
    )

    print(
        "Bot ready for use"
    )


if __name__ == "__main__":
    client.run(
        token
    )