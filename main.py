from dotenv import load_dotenv

import os
import discord

from discord import app_commands

from modules.sprint import SprintCreateModal


load_dotenv()

token = os.getenv("DISCORD_TOKEN")

if token is None:
    raise RuntimeError("DISCORD_TOKEN was not found in the environment.")


intents = discord.Intents.default()

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)


# -------------------------------------------------------
# COMMANDS
# -------------------------------------------------------

@tree.command(
    name="ping",
    description="Check if the bot is responding"
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "What are you doing? Shouldn't you be working?"
    )


@tree.command(
    name="sprint",
    description="Start a writing sprint"
)
async def sprint(interaction: discord.Interaction):
    modal = SprintCreateModal()

    await interaction.response.send_modal(modal)


# -------------------------------------------------------
# DISCORD CONNECTION
# -------------------------------------------------------

@client.event
async def on_ready():
    test_server = discord.Object(
        id=1540358191387513034
    )

    tree.copy_global_to(guild=test_server)

    synced = await tree.sync(
        guild=test_server
    )

    print(f"Synced commands: {len(synced)}")
    print(f"Logged in as: {client.user}")
    print("Bot ready for use")


client.run(token)