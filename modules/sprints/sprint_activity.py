from __future__ import annotations

import asyncio
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .users import SprintUser

import discord

from modules.common.ui import WordCountChangeModal

from .sprint_results import (
    RESULT_REGISTRATION_SECONDS,
    RESULT_REMINDER_SECONDS,
    close_results_registration,
    get_pending_results,
    get_sorted_results,
    send_result_reminder
)

from modules.user_profile.projects import (
    ProjectPickerView,
    update_project
)

from .system_messages import (
    create_finished_embed,
    create_results_embed
)

# -------------------------------------------------------
#                 WORD COUNT CALCULATIONS
# -------------------------------------------------------

def calculate_new_total(
    initial_wc: int,
    new_total: int
):
    return (
        new_total
        - initial_wc
    )


def calculate_difference_total(
    initial_wc: int,
    difference: int
):
    return (
        initial_wc
        + difference
    )


def register_new_total(
    sprint_user: SprintUser,
    new_total: int
):
    current_words = calculate_new_total(
        sprint_user.initial_wc,
        new_total
    )

    sprint_user.final_wc = (
        new_total
    )

    sprint_user.words_written = (
        sprint_user.accumulated_words
        + current_words
    )

    sprint_user.result_registered = True

    update_project(
        user_id=sprint_user.user_id,
        project_id=sprint_user.project_id,
        wordcount=new_total
    )


def register_difference(
    sprint_user: SprintUser,
    difference: int
):
    final_wc = (
        calculate_difference_total(
            sprint_user.initial_wc,
            difference
        )
    )

    sprint_user.final_wc = final_wc

    sprint_user.words_written = (
        sprint_user.accumulated_words
        + difference
    )

    sprint_user.result_registered = True

    update_project(
        user_id=sprint_user.user_id,
        project_id=sprint_user.project_id,
        wordcount=final_wc
    )


# -------------------------------------------------------
#                  ACTIVITY HISTORY
# -------------------------------------------------------

def register_previous_total(
    sprint_user: SprintUser,
    new_total: int
):
    difference = (
        calculate_new_total(
            sprint_user.initial_wc,
            new_total
        )
    )

    sprint_user.archive_activity(
        final_wc=new_total,
        words_written=difference,
        registered=True
    )


def register_previous_difference(
    sprint_user: SprintUser,
    difference: int
):
    final_wc = (
        calculate_difference_total(
            sprint_user.initial_wc,
            difference
        )
    )

    sprint_user.archive_activity(
        final_wc=final_wc,
        words_written=difference,
        registered=True
    )


def skip_previous_activity(
    sprint_user: SprintUser
):
    sprint_user.archive_activity(
        final_wc=None,
        words_written=None,
        registered=False
    )


# -------------------------------------------------------
#                 PROJECT SWITCH VIEW
# -------------------------------------------------------

class ActivityProjectView(
    ProjectPickerView
):
    def __init__(
        self,
        sprint_view,
        sprint_user
    ):
        self.sprint_view = sprint_view
        self.sprint_user = sprint_user

        super().__init__(
            owner_id=sprint_user.user_id,
            on_confirm=self.switch_project
        )

    async def switch_project(
        self,
        interaction,
        project
    ):
        self.sprint_user.switch_project(
            project
        )

        await interaction.response.send_message(
            (
                f"Activity changed to "
                f"**{project['name']}** at "
                f"**{project['wordcount']:,} words**."
            ),
            ephemeral=True
        )

        await self.sprint_view.update_current_message()

        self.stop()


# -------------------------------------------------------
#                 ACTIVITY CHANGE VIEW
# -------------------------------------------------------

class ActivityChangeView(
    discord.ui.View
):
    def __init__(
        self,
        sprint_view,
        sprint_user: SprintUser
    ):
        super().__init__(
            timeout=60
        )

        self.sprint_view = sprint_view
        self.sprint_user = sprint_user

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.sprint_user.user_id
        ):
            await interaction.response.send_message(
                "This activity menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def open_project_picker(
        self,
        interaction
    ):
        view = ActivityProjectView(
            sprint_view=self.sprint_view,
            sprint_user=self.sprint_user
        )

        await interaction.response.send_message(
            "Choose your next project:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(
        label="Register Progress",
        style=discord.ButtonStyle.primary
    )
    async def register_progress(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = WordCountChangeModal(
            initial_total=self.sprint_user.initial_wc,
            on_validated=self.register_progress_result,
            title="Register Current Progress"
        )

        await interaction.response.send_modal(
            modal
        )

    async def register_progress_result(
        self,
        interaction,
        result
    ):
        if result.mode == "total":
            register_previous_total(
                self.sprint_user,
                result.new_total
            )
        else:
            register_previous_difference(
                self.sprint_user,
                result.difference
            )

        view = ActivityProjectView(
            sprint_view=self.sprint_view,
            sprint_user=self.sprint_user
        )

        await interaction.response.send_message(
            "Progress saved. Choose your next project:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(
        label="Skip & Change",
        style=discord.ButtonStyle.secondary
    )
    async def skip_progress(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        skip_previous_activity(
            self.sprint_user
        )

        view = ActivityProjectView(
            sprint_view=self.sprint_view,
            sprint_user=self.sprint_user
        )

        await interaction.response.send_message(
            "Choose your next project:",
            view=view,
            ephemeral=True
        )


# -------------------------------------------------------
#               PREVIOUS ACTIVITY MODAL
# -------------------------------------------------------

# -------------------------------------------------------
#                WORD COUNT MODAL
# -------------------------------------------------------

# -------------------------------------------------------
#                   RESULTS VIEW
# -------------------------------------------------------

class SprintResultsView(
    discord.ui.View
):
    def __init__(
        self,
        participants,
        deadline_timestamp
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

    async def send_final_results(
        self
    ):
        if self.results_sent:
            return

        final_embed = create_results_embed(
            get_sorted_results(
                self.participants
            )
        )

        await self.message.channel.send(
            embed=final_embed
        )

        self.results_sent = True

    async def close_registration_message(
        self
    ):
        if self.message is None:
            return

        await self.message.edit(
            content="Word count registration closed.",
            view=None
        )

    async def finish_if_complete(
        self
    ):
        if self.closed:
            return

        if get_pending_results(
            self.participants
        ):
            return

        self.closed = True

        if self.reminder_task is not None:
            self.reminder_task.cancel()

        if self.close_task is not None:
            self.close_task.cancel()

        await self.close_registration_message()

        await self.send_final_results()

        self.stop()

    @discord.ui.button(
        label="Register Word Count",
        style=discord.ButtonStyle.primary
    )
    async def register_word_count(
        self,
        interaction,
        button
    ):
        if self.closed:
            await interaction.response.send_message(
                "Word count registration is closed.",
                ephemeral=True
            )

            return

        sprint_user = (
            self.participants.get_user(
                interaction.user.id
            )
        )

        if sprint_user is None:
            await interaction.response.send_message(
                "You were not in the sprint when it finished.",
                ephemeral=True
            )

            return

        if sprint_user.result_registered:
            await interaction.response.send_message(
                "You already registered your word count.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            WordCountChangeModal(
                initial_total=sprint_user.initial_wc,
                on_validated=self.register_word_count_result
            )
        )

    async def register_word_count_result(
        self,
        interaction,
        result
    ):
        if result.mode == "total":
            register_new_total(
                self.participants.get_user(
                    interaction.user.id
                ),
                result.new_total
            )
        else:
            register_difference(
                self.participants.get_user(
                    interaction.user.id
                ),
                result.difference
            )

        await interaction.response.send_message(
            "Word count registered.",
            ephemeral=True
        )

        await self.finish_if_complete()


# -------------------------------------------------------
#                 START RESULTS
# -------------------------------------------------------

async def start_results_registration(
    channel,
    duration,
    participants
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

    results_view.message = (
        results_message
    )

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