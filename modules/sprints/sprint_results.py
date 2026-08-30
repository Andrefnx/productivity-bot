import asyncio
import time

import discord

from .system_messages import create_results_embed


WORD_COUNT_REGISTRATION_SECONDS = 600
WORD_COUNT_REMINDER_SECONDS = 120


# -------------------------------------------------------
#                RESULT HELPERS
# -------------------------------------------------------

def get_registered_results(
    participants
):
    return [
        sprint_user
        for sprint_user in participants.get_users()
        if sprint_user.word_count_enabled
        and sprint_user.result_registered
    ]


def get_pending_results(
    participants
):
    return [
        sprint_user
        for sprint_user in participants.get_users()
        if sprint_user.word_count_enabled
        and not sprint_user.result_registered
    ]


def get_sorted_results(
    participants
):
    return sorted(
        get_registered_results(participants),
        key=lambda sprint_user: (
            sprint_user.words_written
            if sprint_user.words_written is not None
            else -999999999
        ),
        reverse=True
    )


# -------------------------------------------------------
#                  RESULTS REGISTRATION
# -------------------------------------------------------

async def send_result_reminder(
    results_view
):
    try:
        await asyncio.sleep(
            results_view.registration_seconds
            - min(
                WORD_COUNT_REMINDER_SECONDS,
                results_view.registration_seconds
            )
        )

        if results_view.closed:
            return

        pending = get_pending_results(
            results_view.participants
        )

        if not pending:
            return

        mentions = " ".join(
            sprint_user.mention
            for sprint_user in pending
        )

        try:
            await results_view.message.channel.send(
                content=(
                    f"{mentions}\n"
                    "2 minutes left to register your word count."
                ),
                allowed_mentions=discord.AllowedMentions(
                    everyone=False,
                    users=True,
                    roles=False
                )
            )
        except (
            discord.Forbidden,
            discord.HTTPException
        ) as error:
            print("SPRINT RESULTS REMINDER ERROR:")
            print(repr(error))

    except asyncio.CancelledError:
        return


async def close_results_registration(
    results_view
):
    try:
        await asyncio.sleep(
            results_view.registration_seconds
        )

        if results_view.closed:
            return

        results_view.closed = True
        await results_view.award_rewards()
        await results_view.close_registration_message()
        await results_view.send_final_results()
        results_view.stop()

    except asyncio.CancelledError:
        return
