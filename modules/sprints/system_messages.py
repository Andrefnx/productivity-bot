import json
import os

import discord


# -------------------------------------------------------
#                   SPRINT STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

ACTIVE_SPRINTS_FILE = os.path.join(
    DATA_DIRECTORY,
    "active_sprints.json"
)


def load_active_sprints():
    if not os.path.exists(
        ACTIVE_SPRINTS_FILE
    ):
        return []

    try:
        with open(
            ACTIVE_SPRINTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):
        return []


def save_active_sprints(
    sprints
):
    os.makedirs(
        DATA_DIRECTORY,
        exist_ok=True
    )

    with open(
        ACTIVE_SPRINTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            sprints,
            file,
            indent=4
        )


def register_active_sprint(
    guild_id,
    channel_id,
    message_id
):
    sprints = load_active_sprints()

    sprint_data = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "message_id": message_id
    }

    sprints = [
        sprint
        for sprint in sprints
        if sprint.get(
            "message_id"
        ) != message_id
    ]

    sprints.append(
        sprint_data
    )

    save_active_sprints(
        sprints
    )


def remove_active_sprint(
    message_id
):
    sprints = load_active_sprints()

    sprints = [
        sprint
        for sprint in sprints
        if sprint.get(
            "message_id"
        ) != message_id
    ]

    save_active_sprints(
        sprints
    )


# -------------------------------------------------------
#                    SPRINT EMBEDS
# -------------------------------------------------------

def create_waiting_embed(
    duration: int,
    start_timestamp: int,
    participants_text: str = "No participants yet.",
    updated: bool = False
):
    if updated:
        description = (
            "Sprint time has been updated.\n"
            "Use the buttons below to join "
            "or modify the sprint."
        )

    else:
        description = (
            "Use the buttons below to join "
            "or modify the sprint."
        )

    embed = discord.Embed(
        title="Productivity time!",
        description=description
    )

    embed.add_field(
        name="Duration",
        value=f"{duration} minutes",
        inline=True
    )

    embed.add_field(
        name="Starts",
        value=f"<t:{start_timestamp}:R>",
        inline=True
    )

    embed.add_field(
        name="Participants",
        value=participants_text,
        inline=False
    )

    return embed


def create_started_embed(
    duration: int,
    end_timestamp: int,
    participants_text: str
):
    embed = discord.Embed(
        title="Sprint started!",
        description=(
            "Time to focus!\n"
            f"Sprint ends <t:{end_timestamp}:R>."
        )
    )

    embed.add_field(
        name="Duration",
        value=f"{duration} minutes",
        inline=True
    )

    embed.add_field(
        name="Participants",
        value=participants_text,
        inline=False
    )

    return embed


def create_ended_embed(
    duration: int,
    participants_text: str
):
    embed = discord.Embed(
        title="Sprint ended!",
        description="Time is up!"
    )

    embed.add_field(
        name="Duration",
        value=f"{duration} minutes",
        inline=True
    )

    embed.add_field(
        name="Participants who finished",
        value=participants_text,
        inline=False
    )

    return embed


def create_cancelled_embed(
    user_mention: str
):
    return discord.Embed(
        title="Sprint cancelled",
        description=(
            "The sprint was cancelled by "
            f"{user_mention}."
        )
    )


def create_interrupted_embed():
    return discord.Embed(
        title="Bot out of order",
        description=(
            "This sprint was interrupted because "
            "the bot went offline.\n\n"
            "Sorry for the inconvenience."
        )
    )


# -------------------------------------------------------
#                 INTERRUPTED SPRINTS
# -------------------------------------------------------

async def mark_message_as_interrupted(
    message: discord.Message
):
    interrupted_embed = create_interrupted_embed()

    await message.edit(
        content=None,
        embed=interrupted_embed,
        view=None
    )


async def recover_saved_sprints(
    client: discord.Client
):
    sprints = load_active_sprints()

    for sprint in sprints:
        channel_id = sprint.get(
            "channel_id"
        )

        message_id = sprint.get(
            "message_id"
        )

        if (
            channel_id is None
            or message_id is None
        ):
            continue

        try:
            channel = client.get_channel(
                channel_id
            )

            if channel is None:
                channel = await client.fetch_channel(
                    channel_id
                )

            message = await channel.fetch_message(
                message_id
            )

            await mark_message_as_interrupted(
                message
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

    save_active_sprints(
        []
    )


async def recover_old_sprints(
    client: discord.Client
):
    active_titles = {
        "Productivity time!",
        "Sprint started!"
    }

    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(
                    limit=200
                ):
                    if message.author.id != client.user.id:
                        continue

                    if not message.embeds:
                        continue

                    embed = message.embeds[0]

                    if embed.title not in active_titles:
                        continue

                    if not message.components:
                        continue

                    try:
                        await mark_message_as_interrupted(
                            message
                        )

                    except (
                        discord.NotFound,
                        discord.Forbidden,
                        discord.HTTPException
                    ):
                        pass

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue


async def recover_interrupted_sprints(
    client: discord.Client
):
    await recover_saved_sprints(
        client
    )

    await recover_old_sprints(
        client
    )