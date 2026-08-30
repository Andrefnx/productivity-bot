import json
import os
import re
import time

import discord

from .messages import (
    cancel_title,
    empty_message,
    empty_title,
    interrupted_message,
    interrupted_title,
    no_results_message,
    registration_message,
    registration_title,
    results_title,
    start_focus_message,
    start_title,
    waiting_message,
    waiting_title,
    waiting_updated_message
)


# -------------------------------------------------------
#                   SPRINT STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

ACTIVE_SPRINTS_FILE = os.path.join(
    DATA_DIRECTORY,
    "active_sprints.json"
)

LIFECYCLE_STATUS_MAP = {
    "scheduled": "countdown",
    "countdown": "countdown",
    "waiting": "countdown",
    "active": "active",
    "running": "active",
    "started": "active",
    "finished": "completed",
    "complete": "completed",
    "completed": "completed",
    "ended": "completed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "interrupted": "interrupted",
    "aborted": "interrupted"
}

TERMINAL_SPRINT_STATUSES = {
    "completed",
    "cancelled",
    "interrupted"
}


def normalize_sprint_status(status):
    return LIFECYCLE_STATUS_MAP.get(
        str(status or "active").lower(),
        "active"
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
    message_id,
    status="countdown",
    start_timestamp=None,
    end_timestamp=None
):
    sprints = load_active_sprints()

    sprint_data = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "message_id": message_id,
        "status": normalize_sprint_status(status),
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp
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


def update_active_sprint_status(
    message_id,
    status,
    start_timestamp=None,
    end_timestamp=None
):
    sprints = load_active_sprints()

    for sprint in sprints:
        if sprint.get("message_id") != message_id:
            continue

        sprint["status"] = normalize_sprint_status(status)
        if start_timestamp is not None:
            sprint["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            sprint["end_timestamp"] = end_timestamp
        break

    save_active_sprints(sprints)


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
#                    WAITING EMBED
# -------------------------------------------------------

def create_waiting_embed(
    duration: int,
    start_timestamp: int,
    participants_text: str = "No participants yet.",
    updated: bool = False
):
    description = (
        waiting_updated_message
        if updated
        else waiting_message
    )

    embed = discord.Embed(
        title=waiting_title,
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


# -------------------------------------------------------
#                    STARTED EMBED
# -------------------------------------------------------

def create_started_embed(
    duration: int,
    end_timestamp: int,
    participants_text: str
):
    embed = discord.Embed(
        title=start_title,
        description=(
            f"{start_focus_message}\n"
            f"Ends <t:{end_timestamp}:R>."
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


# -------------------------------------------------------
#                    FINISHED EMBED
# -------------------------------------------------------

def create_finished_embed(
    duration: int,
    participants_text: str,
    deadline_timestamp: int
):
    embed = discord.Embed(
        title="Sprint finished!",
        description="Time is up!"
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

    embed.add_field(
        name="Register your word count",
        value=(
            f"Registration closes "
            f"<t:{deadline_timestamp}:R>."
        ),
        inline=False
    )

    return embed


# -------------------------------------------------------
#                   CANCELLED EMBED
# -------------------------------------------------------

def create_cancelled_embed(
    user_mention: str
):
    return discord.Embed(
        title=cancel_title,
        description=(
            "The sprint was cancelled by "
            f"**{user_mention}**."
        )
    )


# -------------------------------------------------------
#                     EMPTY EMBED
# -------------------------------------------------------

def create_empty_sprint_embed():
    return discord.Embed(
        title=empty_title,
        description=empty_message
    )


# -------------------------------------------------------
#                    FINAL RESULTS
# -------------------------------------------------------

def create_results_embed(
    sorted_results
):
    embed = discord.Embed(
        title="🏆 Sprint Results"
    )

    if not sorted_results:
        embed.description = no_results_message

        return embed

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    result_blocks = []

    for position, sprint_user in enumerate(
        sorted_results,
        start=1
    ):
        medal = (
            medals[position - 1]
            if position <= 3
            else f"#{position}"
        )

        name = sprint_user.user.display_name

        project = (
            sprint_user.project
            if sprint_user.project
            else "No project"
        )

        if sprint_user.final_wc is None:
            total_text = "unknown"

        else:
            total_text = (
                f"{sprint_user.final_wc:,} words"
            )

        if sprint_user.words_written is None:
            progress_text = (
                "Progress wasn't recorded"
            )

        elif sprint_user.words_written >= 0:
            progress_text = (
                f"*+{sprint_user.words_written:,} words*"
            )

        else:
            progress_text = (
                "There is progress... just backwards\n"
                f"*{sprint_user.words_written:,} words*"
            )

        block = (
            f"{medal} **{name}**\n"
            f"{progress_text}\n"
            f"New total for ***{project}*** "
            f"is **{total_text}**"
        )

        result_blocks.append(
            block
        )

    embed.description = "\n\n".join(
        result_blocks
    )

    return embed

# -------------------------------------------------------
#                  INTERRUPTED EMBED
# -------------------------------------------------------

def create_interrupted_embed():
    return discord.Embed(
        title=interrupted_title,
        description=interrupted_message
    )


def create_completed_embed():
    return discord.Embed(
        title="Sprint finished!",
        description="Time is up!"
    )


# -------------------------------------------------------
#                 INTERRUPTED SPRINTS
# -------------------------------------------------------

async def mark_message_as_interrupted(
    message: discord.Message
):
    interrupted_embed = (
        create_interrupted_embed()
    )

    await message.edit(
        content=None,
        embed=interrupted_embed,
        view=None
    )


def get_message_end_timestamp(message):
    if not message.embeds:
        return None

    embed = message.embeds[0]
    text = "\n".join(
        [embed.description or ""]
        + [field.value for field in embed.fields]
    )
    timestamps = re.findall(r"<t:(\d+):[RFDfdt]>", text)

    if embed.title == start_title and timestamps:
        return int(timestamps[0])

    if embed.title == waiting_title and timestamps:
        duration_match = re.search(r"(\d+) minutes", text)
        if duration_match:
            return int(timestamps[0]) + int(duration_match.group(1)) * 60

    return None


def should_recover_as_completed(sprint, message, now=None):
    now = int(time.time()) if now is None else now
    status = normalize_sprint_status(sprint.get("status"))

    if status in TERMINAL_SPRINT_STATUSES:
        return False

    end_timestamp = sprint.get("end_timestamp")
    if end_timestamp is None:
        end_timestamp = get_message_end_timestamp(message)

    return end_timestamp is not None and now >= int(end_timestamp)


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

            status = normalize_sprint_status(sprint.get("status"))
            if should_recover_as_completed(sprint, message):
                update_active_sprint_status(message_id, "completed")
                await message.edit(
                    content=None,
                    embed=create_completed_embed(),
                    view=None
                )
            elif status not in TERMINAL_SPRINT_STATUSES:
                update_active_sprint_status(message_id, "interrupted")
                await mark_message_as_interrupted(message)

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

async def recover_old_sprints(
    client: discord.Client
):
    active_titles = {
        waiting_title,
        start_title
    }

    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(
                    limit=200
                ):
                    if (
                        message.author.id
                        != client.user.id
                    ):
                        continue

                    if not message.embeds:
                        continue

                    embed = message.embeds[0]

                    if (
                        embed.title
                        not in active_titles
                    ):
                        continue

                    if not message.components:
                        continue

                    try:
                        if should_recover_as_completed({}, message):
                            await message.edit(
                                content=None,
                                embed=create_completed_embed(),
                                view=None
                            )
                        else:
                            await mark_message_as_interrupted(message)

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