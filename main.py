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
    ConfigView,
    create_config_embed
)

from modules.config import (
    get_user_config
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

@tree.command(
    name="sprint",
    description="Start a writing sprint"
)
async def sprint(
    interaction: discord.Interaction
):
    sprint_modal = SprintCreateModal()

    await interaction.response.send_modal(
        sprint_modal
    )


# -------------------------------------------------------
#                       PROFILE
# -------------------------------------------------------

@tree.command(
    name="profile",
    description="Open your profile"
)
async def profile(
    interaction: discord.Interaction
):
    profile_embed = create_profile_embed(
        interaction.user
    )

    profile_view = ProfileView(
        owner=interaction.user
    )

    config = get_user_config(
        interaction.user.id
    )

    is_private = (
        config[
            "profile_visibility"
        ]
        == "private"
    )

    await interaction.response.send_message(
        embed=profile_embed,
        view=profile_view,
        ephemeral=is_private
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
    await interaction.response.send_message(
        embed=create_config_embed(
            interaction.user
        ),
        view=ConfigView(
            owner=interaction.user
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

    test_server = discord.Object(
        id=1541532111687647412
    )

    tree.copy_global_to(
        guild=test_server
    )

    synced = await tree.sync(
        guild=test_server
    )

    print(
        f"Synced commands: {len(synced)}"
    )

    print(
        f"Logged in as: {client.user}"
    )

    print(
        "Bot ready for use"
    )


client.run(
    token
)