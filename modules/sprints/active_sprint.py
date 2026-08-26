import asyncio
import time

import discord

from .system_messages import (
    create_cancelled_embed,
    create_ended_embed,
    create_started_embed,
    create_waiting_embed,
    register_active_sprint,
    remove_active_sprint
)

from .users import SprintParticipants


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

        self.participants = SprintParticipants()

        self.start_timestamp = int(
            time.time()
            + starts_in * 60
        )

        self.started = False


# -------------------------------------------------------
#                  SPRINT MESSAGE
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
            embed=waiting_embed,
            view=self
        )


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

            end_timestamp = int(
                time.time()
                + self.duration * 60
            )

            started_embed = create_started_embed(
                duration=self.duration,
                end_timestamp=end_timestamp,
                participants_text=(
                    self.participants.get_mentions_text()
                )
            )

            start_ping = (
                self.participants.get_start_ping()
            )

            await self.message.edit(
                content=start_ping,
                embed=started_embed,
                view=self
            )

            await asyncio.sleep(
                self.duration * 60
            )

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

        except asyncio.CancelledError:
            raise


# -------------------------------------------------------
#                  RESTART TIMER
# -------------------------------------------------------

    async def restart_timer(
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

        self.started = False

        await self.update_waiting_message(
            updated=True
        )

        self.sprint_timer = asyncio.create_task(
            self.run_sprint()
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

        cancelled_embed = create_cancelled_embed(
            user_mention=interaction.user.mention
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
        if self.started:
            await interaction.response.send_message(
                "This sprint has already started.",
                ephemeral=True
            )

            return

        added = self.participants.add_user(
            interaction.user
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

        await self.update_waiting_message()


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
        if self.started:
            await interaction.response.send_message(
                "This sprint has already started.",
                ephemeral=True
            )

            return

        removed = self.participants.remove_user(
            interaction.user.id
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

        await self.update_waiting_message()


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
        confirmation_view = ConfirmationView(
            confirm_callback=self.confirm_cancel
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
        if self.started:
            await interaction.response.send_message(
                "This sprint has already started.",
                ephemeral=True
            )

            return

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

        self.duration_input = discord.ui.TextInput(
            label="Duration (minutes)",
            default=str(
                sprint_view.duration
            ),
            style=discord.TextStyle.short,
            required=True,
            max_length=3
        )

        self.starts_in_input = discord.ui.TextInput(
            label="Starts in (minutes)",
            default=str(
                sprint_view.starts_in
            ),
            style=discord.TextStyle.short,
            required=True,
            max_length=3
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

            starts_in = int(
                self.starts_in_input.value
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

        await interaction.response.send_message(
            "Sprint time updated!",
            ephemeral=True
        )

        await self.sprint_view.restart_timer(
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

        self.duration_input = discord.ui.TextInput(
            label="Duration (minutes)",
            placeholder="e.g. 30",
            style=discord.TextStyle.short,
            required=True,
            max_length=3
        )

        self.starts_in_input = discord.ui.TextInput(
            label="Starts in (minutes)",
            placeholder="e.g. 10",
            style=discord.TextStyle.short,
            required=False,
            max_length=3
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

        message = await interaction.original_response()

        view.message = message

        register_active_sprint(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            message_id=message.id
        )

        view.sprint_timer = asyncio.create_task(
            view.run_sprint()
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