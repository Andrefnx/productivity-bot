import asyncio
import time
import uuid

import discord

from .messages import (
    already_finished_message,
    already_joined_message,
    already_started_message,
    cancel_back_message,
    cancel_confirmation_message,
    cancelled_response_message,
    create_time_invalid_message,
    duration_invalid_message,
    ending_soon_message,
    ending_soon_submessage,
    force_ended_message,
    force_ending_message,
    force_started_message,
    join_question_message,
    left_message,
    no_test_participants_message,
    not_joined_message,
    start_first_message,
    start_message,
    start_time_invalid_message,
    time_invalid_message,
    time_updated_message
)

from .sprint_activity import (
    start_results_registration
)

from .system_messages import (
    create_cancelled_embed,
    create_empty_sprint_embed,
    create_started_embed,
    create_waiting_embed,
    register_active_sprint,
    remove_active_sprint
)

from .users import (
    JoinSprintView,
    SprintParticipants
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
        await self.confirm_callback(
            interaction
        )

        self.stop()

    @discord.ui.button(
        label="↩️ Go Back",
        style=discord.ButtonStyle.secondary
    )
    async def go_back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content=cancel_back_message,
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

        self.sprint_id = str(
            uuid.uuid4()
        )

        self.duration = duration
        self.starts_in = starts_in

        self.message = None
        self.sprint_timer = None

        self.participants = SprintParticipants(
            sprint_id=self.sprint_id
        )

        self.start_timestamp = int(
            time.time()
            + starts_in * 60
        )

        self.end_timestamp = None

        self.started = False
        self.finished = False


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
        if self.finished:
            return

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
        mentions = self.participants.get_ping_text()

        if not mentions:
            return

        try:
            await self.message.channel.send(
                content=(
                    f"{mentions}\n"
                    f"{start_message}"
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
            print(
                "START NOTIFICATION ERROR:"
            )

            print(
                repr(error)
            )


# -------------------------------------------------------
#                ENDING NOTIFICATION
# -------------------------------------------------------

    async def send_ending_notification(
        self
    ):
        mentions = self.participants.get_ping_text()

        if not mentions:
            return

        try:
            await self.message.channel.send(
                content=(
                    f"{mentions}\n"
                    f"{ending_soon_message}\n"
                    f"{ending_soon_submessage}"
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
            print(
                "ENDING NOTIFICATION ERROR:"
            )

            print(
                repr(error)
            )


# -------------------------------------------------------
#                   START SPRINT
# -------------------------------------------------------

    async def start_sprint(
        self
    ):
        if self.started:
            return

        if self.finished:
            return

        self.started = True

        self.end_timestamp = int(
            time.time()
            + self.duration * 60
        )

        await self.update_started_message()

        await self.send_start_notification()


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

            await self.start_sprint()

            await self.run_active_timer()

        except asyncio.CancelledError:
            return

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

                if self.finished:
                    return

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

            if self.finished:
                return

            await self.finish_sprint()

        except asyncio.CancelledError:
            return


# -------------------------------------------------------
#                  FINISH SPRINT
# -------------------------------------------------------

    async def finish_sprint(
        self
    ):
        if self.finished:
            return

        if len(
            self.participants
        ) == 0:
            await self.close_empty_sprint()

            return

        self.finished = True

        finished_participants = (
            self.participants.snapshot()
        )

        channel = self.message.channel
        message_id = self.message.id

        remove_active_sprint(
            message_id
        )

        try:
            await self.message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        await start_results_registration(
            channel=channel,
            duration=self.duration,
            participants=finished_participants
        )

        self.stop()


# -------------------------------------------------------
#                   EMPTY SPRINT
# -------------------------------------------------------

    async def close_empty_sprint(
        self
    ):
        if self.finished:
            return

        self.finished = True

        empty_embed = create_empty_sprint_embed()

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
        self.finished = False

        await self.update_waiting_message(
            updated=True
        )

        self.sprint_timer = asyncio.create_task(
            self.run_sprint()
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

        self.sprint_timer = asyncio.create_task(
            self.run_active_timer()
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

        self.finished = True

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
            content=cancelled_response_message,
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
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
                ephemeral=True
            )

            return

        if self.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                already_joined_message,
                ephemeral=True
            )

            return

        join_view = JoinSprintView(
            sprint_view=self,
            user_id=interaction.user.id
        )

        await interaction.response.send_message(
            join_question_message,
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
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
                ephemeral=True
            )

            return

        removed = self.participants.remove_user(
            interaction.user.id
        )

        if not removed:
            await interaction.response.send_message(
                not_joined_message,
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            left_message,
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
        confirmation_view = ConfirmationView(
            confirm_callback=self.confirm_cancel
        )

        await interaction.response.send_message(
            cancel_confirmation_message,
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
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
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
#                 TEST FORCE START
# -------------------------------------------------------

    @discord.ui.button(
        label="Force Start",
        style=discord.ButtonStyle.success,
        row=2
    )
    async def force_start(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
                ephemeral=True
            )

            return

        if self.started:
            await interaction.response.send_message(
                already_started_message,
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        await self.start_sprint()

        self.sprint_timer = asyncio.create_task(
            self.run_active_timer()
        )

        await interaction.followup.send(
            force_started_message,
            ephemeral=True
        )

# -------------------------------------------------------
#                  TEST FORCE END
# -------------------------------------------------------

    @discord.ui.button(
        label="Force End",
        style=discord.ButtonStyle.success,
        row=2
    )
    async def force_end(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        if self.sprint_timer is not None:
            self.sprint_timer.cancel()

        await self.finish_sprint()

        await interaction.followup.send(
            force_ended_message,
            ephemeral=True
        )



# -------------------------------------------------------
#                TEST ENDING SOON
# -------------------------------------------------------

    @discord.ui.button(
        label="Ending Soon",
        style=discord.ButtonStyle.success,
        row=2
    )
    async def force_ending_notification(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.finished:
            await interaction.response.send_message(
                already_finished_message,
                ephemeral=True
            )

            return

        if not self.started:
            await interaction.response.send_message(
                start_first_message,
                ephemeral=True
            )

            return

        if len(
            self.participants
        ) == 0:
            await interaction.response.send_message(
                no_test_participants_message,
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        await self.send_ending_notification()

        await interaction.followup.send(
            force_ending_message,
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
            title="⏱️ Change Sprint Time"
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

        self.add_item(
            self.duration_input
        )

        if not sprint_view.started:
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
                time_invalid_message,
                ephemeral=True
            )

            return

        if duration <= 0:
            await interaction.response.send_message(
                duration_invalid_message,
                ephemeral=True
            )

            return

        if (
            starts_in is not None
            and starts_in < 0
        ):
            await interaction.response.send_message(
                start_time_invalid_message,
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            time_updated_message,
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
                time_invalid_message,
                ephemeral=True
            )

            return

        if (
            duration <= 0
            or starts_in < 0
        ):
            await interaction.response.send_message(
                create_time_invalid_message,
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