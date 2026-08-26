import asyncio
import time

import discord

from .messages import (
    registration_already_closed_message,
    registration_closed_message,
    registration_reminder_message,
    wordcount_already_registered_message,
    wordcount_both_message,
    wordcount_difference_invalid_message,
    wordcount_empty_message,
    wordcount_not_participant_message,
    wordcount_registered_message,
    wordcount_result_negative_message,
    wordcount_total_invalid_message,
    wordcount_total_negative_message
)

from .system_messages import (
    create_finished_embed,
    create_results_embed
)

from .users import (
    SprintParticipants,
    SprintUser,
    save_previous_sprint_data
)


RESULT_REGISTRATION_SECONDS = 600
RESULT_REMINDER_SECONDS = 120


# -------------------------------------------------------
#                 WORD COUNT CALCULATIONS
# -------------------------------------------------------

def register_new_total(
    sprint_user: SprintUser,
    new_total: int
):
    sprint_user.final_wc = new_total

    if sprint_user.initial_wc is not None:
        sprint_user.words_written = (
            new_total
            - sprint_user.initial_wc
        )

    else:
        sprint_user.words_written = None

    sprint_user.result_registered = True

    save_previous_sprint_data(
        user_id=sprint_user.user_id,
        initial_wc=sprint_user.final_wc,
        project=sprint_user.project
    )


def register_difference(
    sprint_user: SprintUser,
    difference: int
):
    sprint_user.words_written = difference

    if sprint_user.initial_wc is not None:
        sprint_user.final_wc = (
            sprint_user.initial_wc
            + difference
        )

    else:
        sprint_user.final_wc = None

    sprint_user.result_registered = True

    save_previous_sprint_data(
        user_id=sprint_user.user_id,
        initial_wc=sprint_user.final_wc,
        project=sprint_user.project
    )


# -------------------------------------------------------
#                    RESULT HELPERS
# -------------------------------------------------------

def get_registered_results(
    participants: SprintParticipants
):
    return [
        sprint_user
        for sprint_user
        in participants.get_users()
        if sprint_user.result_registered
    ]


def get_pending_results(
    participants: SprintParticipants
):
    return [
        sprint_user
        for sprint_user
        in participants.get_users()
        if not sprint_user.result_registered
    ]


def get_sorted_results(
    participants: SprintParticipants
):
    results = get_registered_results(
        participants
    )

    return sorted(
        results,
        key=lambda sprint_user: (
            sprint_user.words_written
            if sprint_user.words_written
            is not None
            else -999999999
        ),
        reverse=True
    )


# -------------------------------------------------------
#                WORD COUNT MODAL
# -------------------------------------------------------

class WordCountModal(
    discord.ui.Modal
):
    def __init__(
        self,
        results_view,
        sprint_user: SprintUser
    ):
        super().__init__(
            title="Register Word Count"
        )

        self.results_view = results_view
        self.sprint_user = sprint_user

        self.new_total_input = (
            discord.ui.TextInput(
                label="OPTION 1 — New total word count",
                placeholder="Choose this OR the option below",
                style=discord.TextStyle.short,
                required=False,
                max_length=10
            )
        )

        self.difference_input = (
            discord.ui.TextInput(
                label="OPTION 2 — Words added or removed",
                placeholder="Choose this OR the option above",
                style=discord.TextStyle.short,
                required=False,
                max_length=10
            )
        )

        self.add_item(
            self.new_total_input
        )

        self.add_item(
            self.difference_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        new_total_value = (
            self.new_total_input.value.strip()
        )

        difference_value = (
            self.difference_input.value.strip()
        )

        if (
            not new_total_value
            and not difference_value
        ):
            await interaction.response.send_message(
                wordcount_empty_message,
                ephemeral=True
            )

            return

        if (
            new_total_value
            and difference_value
        ):
            await interaction.response.send_message(
                wordcount_both_message,
                ephemeral=True
            )

            return

        if new_total_value:
            try:
                new_total = int(
                    new_total_value
                )

            except ValueError:
                await interaction.response.send_message(
                    wordcount_total_invalid_message,
                    ephemeral=True
                )

                return

            if new_total < 0:
                await interaction.response.send_message(
                    wordcount_total_negative_message,
                    ephemeral=True
                )

                return

            register_new_total(
                sprint_user=self.sprint_user,
                new_total=new_total
            )

        else:
            try:
                difference = int(
                    difference_value
                )

            except ValueError:
                await interaction.response.send_message(
                    wordcount_difference_invalid_message,
                    ephemeral=True
                )

                return

            if (
                self.sprint_user.initial_wc
                is not None
                and (
                    self.sprint_user.initial_wc
                    + difference
                ) < 0
            ):
                await interaction.response.send_message(
                    wordcount_result_negative_message,
                    ephemeral=True
                )

                return

            register_difference(
                sprint_user=self.sprint_user,
                difference=difference
            )

        await interaction.response.send_message(
            wordcount_registered_message,
            ephemeral=True
        )

        await self.results_view.finish_if_complete()


# -------------------------------------------------------
#                   RESULTS VIEW
# -------------------------------------------------------

class SprintResultsView(
    discord.ui.View
):
    def __init__(
        self,
        participants: SprintParticipants,
        deadline_timestamp: int
    ):
        super().__init__(
            timeout=None
        )

        self.participants = participants
        self.deadline_timestamp = deadline_timestamp

        self.message = None

        self.closed = False
        self.results_sent = False

        self.reminder_task = None
        self.close_task = None


# -------------------------------------------------------
#                   FINAL RESULTS
# -------------------------------------------------------

    async def send_final_results(
        self
    ):
        if self.results_sent:
            return

        sorted_results = get_sorted_results(
            self.participants
        )

        final_embed = create_results_embed(
            sorted_results
        )

        try:
            await self.message.channel.send(
                embed=final_embed
            )

            self.results_sent = True

        except (
            discord.Forbidden,
            discord.HTTPException
        ) as error:
            print(
                "FINAL RESULTS ERROR:"
            )

            print(
                repr(error)
            )


# -------------------------------------------------------
#                  CLOSE REGISTRATION
# -------------------------------------------------------

    async def close_registration_message(
        self
    ):
        if self.message is None:
            return

        try:
            await self.message.edit(
                content=registration_closed_message,
                view=None
            )

        except discord.HTTPException as error:
            print(
                "REGISTRATION CLOSE ERROR:"
            )

            print(
                repr(error)
            )


# -------------------------------------------------------
#                FINISH IF COMPLETE
# -------------------------------------------------------

    async def finish_if_complete(
        self
    ):
        if self.closed:
            return

        pending = get_pending_results(
            self.participants
        )

        if pending:
            return

        self.closed = True

        if self.reminder_task is not None:
            self.reminder_task.cancel()

        if self.close_task is not None:
            self.close_task.cancel()

        await self.close_registration_message()

        await self.send_final_results()

        self.stop()


# -------------------------------------------------------
#              REGISTER WORD COUNT BUTTON
# -------------------------------------------------------

    @discord.ui.button(
        label="Register Word Count",
        style=discord.ButtonStyle.primary
    )
    async def register_word_count(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.closed:
            await interaction.response.send_message(
                registration_already_closed_message,
                ephemeral=True
            )

            return

        sprint_user = self.participants.get_user(
            interaction.user.id
        )

        if sprint_user is None:
            await interaction.response.send_message(
                wordcount_not_participant_message,
                ephemeral=True
            )

            return

        if sprint_user.result_registered:
            await interaction.response.send_message(
                wordcount_already_registered_message,
                ephemeral=True
            )

            return

        modal = WordCountModal(
            results_view=self,
            sprint_user=sprint_user
        )

        await interaction.response.send_modal(
            modal
        )


# -------------------------------------------------------
#                  RESULT REMINDER
# -------------------------------------------------------

async def send_result_reminder(
    results_view: SprintResultsView
):
    try:
        await asyncio.sleep(
            RESULT_REGISTRATION_SECONDS
            - RESULT_REMINDER_SECONDS
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
            for sprint_user
            in pending
        )

        await results_view.message.channel.send(
            content=(
                f"{mentions}\n"
                f"{registration_reminder_message}"
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False
            )
        )

    except asyncio.CancelledError:
        return

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:
        print(
            "RESULT REMINDER ERROR:"
        )

        print(
            repr(error)
        )


# -------------------------------------------------------
#                 CLOSE RESULTS
# -------------------------------------------------------

async def close_results_registration(
    results_view: SprintResultsView
):
    try:
        await asyncio.sleep(
            RESULT_REGISTRATION_SECONDS
        )

        if results_view.closed:
            return

        results_view.closed = True

        await results_view.close_registration_message()

        await results_view.send_final_results()

        results_view.stop()

    except asyncio.CancelledError:
        return


# -------------------------------------------------------
#                 START RESULTS
# -------------------------------------------------------

async def start_results_registration(
    channel,
    duration: int,
    participants: SprintParticipants
):
    mentions = (
        participants.get_ping_text()
    )

    if not mentions:
        return

    deadline_timestamp = int(
        time.time()
        + RESULT_REGISTRATION_SECONDS
    )

    results_view = SprintResultsView(
        participants=participants,
        deadline_timestamp=deadline_timestamp
    )

    finished_embed = create_finished_embed(
        duration=duration,
        participants_text=(
            participants.get_mentions_text()
        ),
        deadline_timestamp=deadline_timestamp
    )

    try:
        results_message = await channel.send(
            content=mentions,
            embed=finished_embed,
            view=results_view,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False
            )
        )

        results_view.message = results_message

        results_view.reminder_task = (
            asyncio.create_task(
                send_result_reminder(
                    results_view
                )
            )
        )

        results_view.close_task = (
            asyncio.create_task(
                close_results_registration(
                    results_view
                )
            )
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:
        print(
            "RESULTS MESSAGE ERROR:"
        )

        print(
            repr(error)
        )