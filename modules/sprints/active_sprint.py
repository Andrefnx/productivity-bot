import asyncio
import time

import discord

from .system_messages import (
    create_cancelled_embed,
    create_empty_sprint_embed,
    create_ended_embed,
    create_started_embed,
    create_waiting_embed,
    register_active_sprint,
    remove_active_sprint
)

from .users import (
    SprintParticipants,
    get_previous_sprint_data
)


# -------------------------------------------------------
#                CONFIRMATION VIEW
# -------------------------------------------------------

class ConfirmationView(
    discord.ui.View
):
    def __init__(
        self,
        confirm_callback
    ):
        super().__init__(
            timeout=30
        )

        self.confirm_callback = (
            confirm_callback
        )

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.confirm_callback(
            interaction
        )

        self.stop()

    @discord.ui.button(
        label="Go Back",
        style=discord.ButtonStyle.secondary
    )
    async def go_back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="Action cancelled.",
            view=None
        )

        self.stop()


class JoinSprintView(
    discord.ui.View
):
    def __init__(
        self,
        sprint_view,
        user_id: int
    ):
        super().__init__(
            timeout=60
        )

        self.sprint_view = sprint_view
        self.user_id = user_id

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This join menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Enter Details",
        style=discord.ButtonStyle.primary
    )
    async def enter_details(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.sprint_view.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        modal = JoinSprintModal(
            sprint_view=self.sprint_view,
            user_id=interaction.user.id
        )

        await interaction.response.send_modal(
            modal
        )

    @discord.ui.button(
        label="Use Previous",
        style=discord.ButtonStyle.secondary
    )
    async def use_previous(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.sprint_view.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        previous_data = get_previous_sprint_data(
            interaction.user.id
        )

        if previous_data is None:
            await interaction.response.send_message(
                "You don't have previous sprint data yet.",
                ephemeral=True
            )

            return

        added = self.sprint_view.participants.add_user(
            user=interaction.user,
            initial_wc=previous_data.get(
                "initial_wc"
            ),
            project=previous_data.get(
                "project"
            )
        )

        if not added:
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content="You joined the sprint!",
            view=None
        )

        await self.sprint_view.update_current_message()

        self.stop()


# -------------------------------------------------------
#                    JOIN MODAL
# -------------------------------------------------------

class JoinSprintModal(
    discord.ui.Modal
):
    def __init__(
        self,
        sprint_view,
        user_id: int
    ):
        super().__init__(
            title="Join Sprint"
        )

        self.sprint_view = sprint_view
        self.user_id = user_id

        self.initial_wc_input = discord.ui.TextInput(
            label="Initial word count",
            placeholder="e.g. 1932",
            style=discord.TextStyle.short,
            required=False,
            max_length=10
        )

        self.project_input = discord.ui.TextInput(
            label="Project",
            placeholder="e.g. Big Bang 2026",
            style=discord.TextStyle.short,
            required=False,
            max_length=100
        )

        self.add_item(
            self.initial_wc_input
        )

        self.add_item(
            self.project_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This join form belongs to another user.",
                ephemeral=True
            )

            return

        if self.sprint_view.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        initial_wc = None

        if self.initial_wc_input.value:
            try:
                initial_wc = int(
                    self.initial_wc_input.value
                )

            except ValueError:
                await interaction.response.send_message(
                    "Word count must be a number.",
                    ephemeral=True
                )

                return

            if initial_wc < 0:
                await interaction.response.send_message(
                    "Word count cannot be negative.",
                    ephemeral=True
                )

                return

        project = (
            self.project_input.value.strip()
            or None
        )

        added = self.sprint_view.participants.add_user(
            user=interaction.user,
            initial_wc=initial_wc,
            project=project
        )

        if not added:
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "You joined the sprint!",
            ephemeral=True
        )

        await self.sprint_view.update_current_message()


# -------------------------------------------------------
#                    SPRINT VIEW
# -------------------------------------------------------

class SprintView(
    discord.ui.View
):
    def __init__(
        self,
        duration: int,
        starts_in: int
    ):
        super().__init__(
            timeout=None
        )

        self.duration = duration
        self.starts_in = starts_in

        self.message = None
        self.sprint_timer = None

        self.participants = (
            SprintParticipants()
        )

        self.start_timestamp = int(
            time.time()
            + starts_in * 60
        )

        self.end_timestamp = None
        self.started = False



# -------------------------------------------------------
#                  WAITING MESSAGE
# -------------------------------------------------------

    async def update_waiting_message(
        self,
        updated: bool = False
    ):
        waiting_embed = create_waiting_embed(
            duration=self.duration,
            start_timestamp=self.start_timestamp,
            participants_text=(
                self.participants.get_mentions_text()
            ),
            updated=updated
        )

        await self.message.edit(
            content=None,
            embed=waiting_embed,
            view=self
        )


# -------------------------------------------------------
#                  STARTED MESSAGE
# -------------------------------------------------------

    async def update_started_message(
        self
    ):
        started_embed = create_started_embed(
            duration=self.duration,
            end_timestamp=self.end_timestamp,
            participants_text=(
                self.participants.get_mentions_text()
            )
        )

        await self.message.edit(
            content=None,
            embed=started_embed,
            view=self
        )


# -------------------------------------------------------
#                  CURRENT MESSAGE
# -------------------------------------------------------

    async def update_current_message(
        self
    ):
        if self.started:
            await self.update_started_message()

        else:
            await self.update_waiting_message()


# -------------------------------------------------------
#                START NOTIFICATION
# -------------------------------------------------------

    async def send_start_notification(
        self
    ):
        start_ping = (
            self.participants.get_start_ping()
        )

        if not start_ping:
            return False

        try:
            await self.message.channel.send(
                content=(
                    f"{start_ping}\n"
                    "Sprint started!"
                ),
                allowed_mentions=discord.AllowedMentions(
                    everyone=False,
                    users=True,
                    roles=False
                )
            )

            return True

        except (
            discord.Forbidden,
            discord.HTTPException
        ) as error:
            print(
                "START NOTIFICATION ERROR:"
            )

            print(
                repr(error)
            )

            return False


# -------------------------------------------------------
#                   SPRINT TIMER
# -------------------------------------------------------

    async def run_sprint(
        self
    ):
        try:
            await asyncio.sleep(
                self.starts_in * 60
            )

            self.started = True

            self.end_timestamp = int(
                time.time()
                + self.duration * 60
            )

            await self.update_started_message()

            await self.send_start_notification()

            await self.run_active_timer()

        except asyncio.CancelledError:
            raise

        except Exception as error:
            print(
                "ERROR IN SPRINT TIMER:"
            )

            print(
                repr(error)
            )


# -------------------------------------------------------
#                  ACTIVE TIMER
# -------------------------------------------------------

    async def run_active_timer(
        self
    ):
        try:
            duration_seconds = (
                self.duration * 60
            )

            if len(
                self.participants
            ) == 0:
                empty_timeout = min(
                    duration_seconds,
                    600
                )

                await asyncio.sleep(
                    empty_timeout
                )

                if len(
                    self.participants
                ) == 0:
                    await self.close_empty_sprint()

                    return

                remaining_seconds = (
                    duration_seconds
                    - empty_timeout
                )

                if remaining_seconds > 0:
                    await asyncio.sleep(
                        remaining_seconds
                    )

            else:
                await asyncio.sleep(
                    duration_seconds
                )

            await self.finish_sprint()

        except asyncio.CancelledError:
            raise


# -------------------------------------------------------
#                  FINISH SPRINT
# -------------------------------------------------------

    async def finish_sprint(
        self
    ):
        if len(
            self.participants
        ) == 0:
            await self.close_empty_sprint()

            return

        ended_embed = create_ended_embed(
            duration=self.duration,
            participants_text=(
                self.participants.get_mentions_text()
            )
        )

        await self.message.edit(
            content=None,
            embed=ended_embed,
            view=None
        )

        remove_active_sprint(
            self.message.id
        )

        self.stop()


# -------------------------------------------------------
#                   EMPTY SPRINT
# -------------------------------------------------------

    async def close_empty_sprint(
        self
    ):
        empty_embed = (
            create_empty_sprint_embed()
        )

        await self.message.edit(
            content=None,
            embed=empty_embed,
            view=None
        )

        remove_active_sprint(
            self.message.id
        )

        self.stop()


# -------------------------------------------------------
#                RESTART WAITING TIMER
# -------------------------------------------------------

    async def restart_waiting_timer(
        self,
        duration: int,
        starts_in: int
    ):
        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        self.duration = duration
        self.starts_in = starts_in

        self.start_timestamp = int(
            time.time()
            + starts_in * 60
        )

        self.end_timestamp = None
        self.started = False

        await self.update_waiting_message(
            updated=True
        )

        self.sprint_timer = (
            asyncio.create_task(
                self.run_sprint()
            )
        )


# -------------------------------------------------------
#                RESTART ACTIVE TIMER
# -------------------------------------------------------

    async def restart_active_timer(
        self,
        duration: int
    ):
        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        self.duration = duration

        self.end_timestamp = int(
            time.time()
            + duration * 60
        )

        await self.update_started_message()

        self.sprint_timer = (
            asyncio.create_task(
                self.run_active_timer()
            )
        )


# -------------------------------------------------------
#                   CANCEL SPRINT
# -------------------------------------------------------

    async def confirm_cancel(
        self,
        interaction: discord.Interaction
    ):
        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        cancelled_embed = (
            create_cancelled_embed(
                user_mention=(
                    interaction.user.mention
                )
            )
        )

        if self.message is not None:
            await self.message.edit(
                content=None,
                embed=cancelled_embed,
                view=None
            )

            remove_active_sprint(
                self.message.id
            )

        await interaction.response.edit_message(
            content="Sprint cancelled.",
            view=None
        )

        self.stop()


# -------------------------------------------------------
#                      JOIN
# -------------------------------------------------------

    @discord.ui.button(
        label="Join",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        join_view = JoinSprintView(
            sprint_view=self,
            user_id=interaction.user.id
        )

        await interaction.response.send_message(
            "How do you want to join?",
            view=join_view,
            ephemeral=True
        )


# -------------------------------------------------------
#                      LEAVE
# -------------------------------------------------------

    @discord.ui.button(
        label="Leave",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        removed = (
            self.participants.remove_user(
                interaction.user.id
            )
        )

        if not removed:
            await interaction.response.send_message(
                "You are not in this sprint.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "You left the sprint!",
            ephemeral=True
        )

        await self.update_current_message()


# -------------------------------------------------------
#                  CANCEL BUTTON
# -------------------------------------------------------

    @discord.ui.button(
        label="Cancel Sprint",
        style=discord.ButtonStyle.danger,
        row=0
    )
    async def cancel_sprint(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        confirmation_view = (
            ConfirmationView(
                confirm_callback=(
                    self.confirm_cancel
                )
            )
        )

        await interaction.response.send_message(
            "Are you sure you want to cancel this sprint?",
            view=confirmation_view,
            ephemeral=True
        )


# -------------------------------------------------------
#                CHANGE SPRINT TIME
# -------------------------------------------------------

    @discord.ui.button(
        label="Change Sprint Time",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def change_sprint_time(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = SprintTimeModal(
            self
        )

        await interaction.response.send_modal(
            modal
        )


# -------------------------------------------------------
#                 SPRINT ACTIVITY
# -------------------------------------------------------

    @discord.ui.button(
        label="Edit Sprint Activity",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def sprint_activity(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Sprint activity editing is coming soon!",
            ephemeral=True
        )


# -------------------------------------------------------
#                    TEST PING
# -------------------------------------------------------

    @discord.ui.button(
        label="Test Ping",
        style=discord.ButtonStyle.success,
        row=2
    )
    async def test_ping(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if len(
            self.participants
        ) == 0:
            await interaction.response.send_message(
                "There are no participants to ping.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        success = (
            await self.send_start_notification()
        )

        if success:
            await interaction.followup.send(
                "Ping sent.",
                ephemeral=True
            )

        else:
            await interaction.followup.send(
                "Ping failed.",
                ephemeral=True
            )


# -------------------------------------------------------
#                 CHANGE SPRINT TIME MODAL
# -------------------------------------------------------

class SprintTimeModal(
    discord.ui.Modal
):
    def __init__(
        self,
        sprint_view: SprintView
    ):
        super().__init__(
            title="Change Sprint Time"
        )

        self.sprint_view = sprint_view

        self.duration_input = (
            discord.ui.TextInput(
                label="Duration (minutes)",
                default=str(
                    sprint_view.duration
                ),
                style=discord.TextStyle.short,
                required=True,
                max_length=3
            )
        )

        self.add_item(
            self.duration_input
        )

        if not sprint_view.started:
            self.starts_in_input = (
                discord.ui.TextInput(
                    label="Starts in (minutes)",
                    default=str(
                        sprint_view.starts_in
                    ),
                    style=discord.TextStyle.short,
                    required=True,
                    max_length=3
                )
            )

            self.add_item(
                self.starts_in_input
            )

        else:
            self.starts_in_input = None

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            duration = int(
                self.duration_input.value
            )

            if self.starts_in_input is not None:
                starts_in = int(
                    self.starts_in_input.value
                )

            else:
                starts_in = None

        except ValueError:
            await interaction.response.send_message(
                "Duration and start time must be numbers.",
                ephemeral=True
            )

            return

        if duration <= 0:
            await interaction.response.send_message(
                "Duration must be greater than 0.",
                ephemeral=True
            )

            return

        if (
            starts_in is not None
            and starts_in < 0
        ):
            await interaction.response.send_message(
                "Start time cannot be negative.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "Sprint time updated!",
            ephemeral=True
        )

        if self.sprint_view.started:
            await self.sprint_view.restart_active_timer(
                duration
            )

        else:
            await self.sprint_view.restart_waiting_timer(
                duration,
                starts_in
            )


# -------------------------------------------------------
#                  SPRINT CREATE MODAL
# -------------------------------------------------------

class SprintCreateModal(
    discord.ui.Modal
):
    def __init__(
        self
    ):
        super().__init__(
            title="Create a Sprint"
        )

        self.duration_input = (
            discord.ui.TextInput(
                label="Duration (minutes)",
                placeholder="e.g. 30",
                style=discord.TextStyle.short,
                required=True,
                max_length=3
            )
        )

        self.starts_in_input = (
            discord.ui.TextInput(
                label="Starts in (minutes)",
                placeholder="e.g. 10",
                style=discord.TextStyle.short,
                required=False,
                max_length=3
            )
        )

        self.add_item(
            self.duration_input
        )

        self.add_item(
            self.starts_in_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            duration = int(
                self.duration_input.value
            )

            starts_in = (
                int(
                    self.starts_in_input.value
                )
                if self.starts_in_input.value
                else 0
            )

        except ValueError:
            await interaction.response.send_message(
                "Duration and start time must be numbers.",
                ephemeral=True
            )

            return

        if (
            duration <= 0
            or starts_in < 0
        ):
            await interaction.response.send_message(
                "Duration must be greater than 0, and start time cannot be negative.",
                ephemeral=True
            )

            return

        start_timestamp = int(
            time.time()
            + starts_in * 60
        )

        waiting_embed = create_waiting_embed(
            duration=duration,
            start_timestamp=start_timestamp
        )

        view = SprintView(
            duration=duration,
            starts_in=starts_in
        )

        await interaction.response.send_message(
            embed=waiting_embed,
            view=view
        )

        message = (
            await interaction.original_response()
        )

        view.message = message

        register_active_sprint(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            message_id=message.id
        )

        view.sprint_timer = (
            asyncio.create_task(
                view.run_sprint()
            )
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception
    ):
        print(
            "ERROR IN SPRINT MODAL:"
        )

        print(
            repr(error)
        )