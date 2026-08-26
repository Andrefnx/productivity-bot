from dotenv import load_dotenv

import os

import discord

from discord import app_commands

from modules.sprints import (
    SprintCreateModal,
    recover_interrupted_sprints
)


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