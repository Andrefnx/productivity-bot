import asyncio
import time

import discord


# -------------------------------------------------------
#                CONFIRMATION VIEW
# -------------------------------------------------------

class ConfirmationView(discord.ui.View):
    def __init__(self, confirm_callback):
        super().__init__(timeout=30)

        self.confirm_callback = confirm_callback

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.confirm_callback(interaction)
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

class SprintView(discord.ui.View):
    def __init__(
        self,
        duration: int,
        starts_in: int
    ):
        super().__init__(timeout=None)

        self.duration = duration
        self.starts_in = starts_in

        self.message = None
        self.sprint_timer = None

    async def run_sprint(self):
        # WAITING -> STARTED
        await asyncio.sleep(self.starts_in * 60)

        end_timestamp = int(
            time.time() + self.duration * 60
        )

        started_embed = discord.Embed(
            title="Sprint started!",
            description=(
                f"Time to focus!\n"
                f"Sprint ends <t:{end_timestamp}:R>."
            )
        )

        started_embed.add_field(
            name="Duration",
            value=f"{self.duration} minutes",
            inline=True
        )

        started_embed.add_field(
            name="Participants",
            value="0",
            inline=False
        )

        await self.message.edit(
            embed=started_embed,
            view=self
        )

        # STARTED -> ENDED
        await asyncio.sleep(self.duration * 60)

        ended_embed = discord.Embed(
            title="Sprint ended!",
            description="Time is up!"
        )

        ended_embed.add_field(
            name="Duration",
            value=f"{self.duration} minutes",
            inline=True
        )

        ended_embed.add_field(
            name="Participants who finished",
            value="0",
            inline=False
        )

        await self.message.edit(
            embed=ended_embed,
            view=None
        )

        self.stop()

    async def restart_timer(
        self,
        duration: int,
        starts_in: int
    ):
        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        self.duration = duration
        self.starts_in = starts_in

        start_timestamp = int(
            time.time() + starts_in * 60
        )

        waiting_embed = discord.Embed(
            title="Productivity time!",
            description=(
                "Sprint time has been updated.\n"
                "Use the buttons below to join or modify the sprint."
            )
        )

        waiting_embed.add_field(
            name="Duration",
            value=f"{duration} minutes",
            inline=True
        )

        waiting_embed.add_field(
            name="Starts",
            value=f"<t:{start_timestamp}:R>",
            inline=True
        )

        waiting_embed.add_field(
            name="Participants",
            value="0",
            inline=False
        )

        await self.message.edit(
            embed=waiting_embed,
            view=self
        )

        self.sprint_timer = asyncio.create_task(
            self.run_sprint()
        )

    async def confirm_cancel(
        self,
        interaction: discord.Interaction
    ):
        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        cancelled_embed = discord.Embed(
            title="Sprint cancelled",
            description=(
                f"The sprint was cancelled by "
                f"{interaction.user.mention}."
            )
        )

        if self.message is not None:
            await self.message.edit(
                embed=cancelled_embed,
                view=None
            )

        await interaction.response.edit_message(
            content="Sprint cancelled.",
            view=None
        )

        self.stop()

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
        await interaction.response.send_message(
            "You joined the sprint!",
            ephemeral=True
        )

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
        await interaction.response.send_message(
            "You left the sprint!",
            ephemeral=True
        )

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
        modal = SprintTimeModal(self)

        await interaction.response.send_modal(
            modal
        )

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

class SprintTimeModal(discord.ui.Modal):
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
            default=str(sprint_view.duration),
            style=discord.TextStyle.short,
            required=True,
            max_length=3
        )

        self.starts_in_input = discord.ui.TextInput(
            label="Starts in (minutes)",
            default=str(sprint_view.starts_in),
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

        if duration <= 0 or starts_in < 0:
            await interaction.response.send_message(
                "Duration must be greater than 0, "
                "and start time cannot be negative.",
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

class SprintCreateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Create a Writing Sprint"
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
                int(self.starts_in_input.value)
                if self.starts_in_input.value
                else 0
            )

        except ValueError:
            await interaction.response.send_message(
                "Duration and start time must be numbers.",
                ephemeral=True
            )
            return

        if duration <= 0 or starts_in < 0:
            await interaction.response.send_message(
                "Duration must be greater than 0, "
                "and start time cannot be negative.",
                ephemeral=True
            )
            return

        start_timestamp = int(
            time.time() + starts_in * 60
        )

        waiting_embed = discord.Embed(
            title="Productivity time!",
            description=(
                "Use the buttons below to join "
                "or modify the sprint."
            )
        )

        waiting_embed.add_field(
            name="Duration",
            value=f"{duration} minutes",
            inline=True
        )

        waiting_embed.add_field(
            name="Starts",
            value=f"<t:{start_timestamp}:R>",
            inline=True
        )

        waiting_embed.add_field(
            name="Participants",
            value="0",
            inline=False
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

        view.sprint_timer = asyncio.create_task(
            view.run_sprint()
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception
    ):
        print("ERROR IN SPRINT MODAL:")
        print(repr(error))