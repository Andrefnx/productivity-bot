import argparse
import asyncio
import os

import discord
from discord import app_commands
from dotenv import load_dotenv


OBSOLETE_COMMANDS = {"market", "ping"}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Remove legacy application commands from one Discord guild."
    )
    parser.add_argument(
        "--guild-id",
        type=int,
        required=True,
        help="Discord guild ID whose legacy commands should be removed."
    )
    return parser.parse_args()


async def remove_legacy_commands(guild_id: int):
    intents = discord.Intents.none()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @client.event
    async def on_ready():
        guild = discord.Object(id=guild_id)
        commands = await tree.fetch_commands(guild=guild)
        obsolete = [
            command
            for command in commands
            if command.name in OBSOLETE_COMMANDS
        ]

        for command in obsolete:
            await command.delete()
            print(
                f"Removed guild command: /{command.name}"
            )

        if not obsolete:
            print("No legacy guild commands found.")

        await client.close()

    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        raise RuntimeError(
            "DISCORD_TOKEN was not found in the environment."
        )

    await client.start(token)


def main():
    load_dotenv()
    arguments = parse_arguments()
    asyncio.run(
        remove_legacy_commands(arguments.guild_id)
    )


if __name__ == "__main__":
    main()