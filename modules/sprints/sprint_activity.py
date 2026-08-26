import asyncio
import time

import discord

from modules.user_profile.projects import (
    ProjectPickerView,
    update_project
)

from .system_messages import (
    create_finished_embed,
    create_results_embed
)

RESULT_REGISTRATION_SECONDS = 600
RESULT_REMINDER_SECONDS = 120


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
        modal = PreviousActivityModal(
            sprint_view=self.sprint_view,
            sprint_user=self.sprint_user
        )

        await interaction.response.send_modal(
            modal
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

class PreviousActivityModal(
    discord.ui.Modal
):
    def __init__(
        self,
        sprint_view,
        sprint_user
    ):
        super().__init__(
            title="Register Current Progress"
        )

        self.sprint_view = sprint_view
        self.sprint_user = sprint_user

        self.new_total_input = (
            discord.ui.TextInput(
                label="OPTION 1 — New total word count",
                placeholder="Choose this OR the option below",
                required=False,
                max_length=10
            )
        )

        self.difference_input = (
            discord.ui.TextInput(
                label="OPTION 2 — Words added or removed",
                placeholder="Choose this OR the option above",
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
                "Pick one option.",
                ephemeral=True
            )

            return

        if (
            new_total_value
            and difference_value
        ):
            await interaction.response.send_message(
                "Pick only one option.",
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
                    "New total must be a number.",
                    ephemeral=True
                )

                return

            if new_total < 0:
                await interaction.response.send_message(
                    "New total cannot be negative.",
                    ephemeral=True
                )

                return

            register_previous_total(
                self.sprint_user,
                new_total
            )

        else:
            try:
                difference = int(
                    difference_value
                )

            except ValueError:
                await interaction.response.send_message(
                    "Use a number like +234 or -120.",
                    ephemeral=True
                )

                return

            final_wc = (
                calculate_difference_total(
                    self.sprint_user.initial_wc,
                    difference
                )
            )

            if final_wc < 0:
                await interaction.response.send_message(
                    "That would make your project total negative.",
                    ephemeral=True
                )

                return

            register_previous_difference(
                self.sprint_user,
                difference
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


# -------------------------------------------------------
#                    RESULT HELPERS
# -------------------------------------------------------

def get_registered_results(
    participants
):
    return [
        sprint_user
        for sprint_user
        in participants.get_users()
        if sprint_user.result_registered
    ]


def get_pending_results(
    participants
):
    return [
        sprint_user
        for sprint_user
        in participants.get_users()
        if not sprint_user.result_registered
    ]


def get_sorted_results(
    participants
):
    return sorted(
        get_registered_results(
            participants
        ),
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
        sprint_user
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
                required=False,
                max_length=10
            )
        )

        self.difference_input = (
            discord.ui.TextInput(
                label="OPTION 2 — Words added or removed",
                placeholder="Choose this OR the option above",
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
        interaction
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
                "Pick one option.",
                ephemeral=True
            )

            return

        if (
            new_total_value
            and difference_value
        ):
            await interaction.response.send_message(
                "Pick only one option.",
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
                    "New total must be a number.",
                    ephemeral=True
                )

                return

            if new_total < 0:
                await interaction.response.send_message(
                    "New total cannot be negative.",
                    ephemeral=True
                )

                return

            register_new_total(
                self.sprint_user,
                new_total
            )

        else:
            try:
                difference = int(
                    difference_value
                )

            except ValueError:
                await interaction.response.send_message(
                    "Use a number like +234 or -120.",
                    ephemeral=True
                )

                return

            final_wc = (
                calculate_difference_total(
                    self.sprint_user.initial_wc,
                    difference
                )
            )

            if final_wc < 0:
                await interaction.response.send_message(
                    "That would make your total negative.",
                    ephemeral=True
                )

                return

            register_difference(
                self.sprint_user,
                difference
            )

        await interaction.response.send_message(
            "Word count registered.",
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
            WordCountModal(
                self,
                sprint_user
            )
        )


# -------------------------------------------------------
#                  RESULT REMINDER
# -------------------------------------------------------

async def send_result_reminder(
    results_view
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
                "2 minutes left to register your word count."
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False
            )
        )

    except asyncio.CancelledError:
        return


# -------------------------------------------------------
#                 CLOSE RESULTS
# -------------------------------------------------------

async def close_results_registration(
    results_view
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