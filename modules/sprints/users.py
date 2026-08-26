import json
import os
import uuid

import discord

from .messages import (
    already_joined_message,
    joined_message,
    join_form_owner_message,
    join_menu_owner_message,
    no_participants_message,
    no_previous_data_message
)


# -------------------------------------------------------
#                    USER STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

SPRINT_USERS_FILE = os.path.join(
    DATA_DIRECTORY,
    "sprint_users.json"
)


def load_sprint_users():
    if not os.path.exists(
        SPRINT_USERS_FILE
    ):
        return {}

    try:
        with open(
            SPRINT_USERS_FILE,
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
        return {}


def save_sprint_users(
    users
):
    os.makedirs(
        DATA_DIRECTORY,
        exist_ok=True
    )

    with open(
        SPRINT_USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            users,
            file,
            indent=4
        )


def save_previous_sprint_data(
    user_id: int,
    initial_wc,
    project
):
    users = load_sprint_users()

    users[str(user_id)] = {
        "initial_wc": initial_wc,
        "project": project
    }

    save_sprint_users(
        users
    )


def get_previous_sprint_data(
    user_id: int
):
    users = load_sprint_users()

    return users.get(
        str(user_id)
    )


# -------------------------------------------------------
#                     SPRINT USER
# -------------------------------------------------------

class SprintUser:
    def __init__(
        self,
        user: discord.User | discord.Member,
        sprint_id: str,
        initial_wc=None,
        project=None
    ):
        self.user = user
        self.user_id = user.id

        self.sprint_id = sprint_id

        self.sprint_user_id = (
            f"{sprint_id}:{user.id}"
        )

        self.session_id = str(
            uuid.uuid4()
        )

        self.initial_wc = initial_wc
        self.final_wc = None
        self.words_written = None

        self.result_registered = False

        self.project = (
            project.strip()
            if project
            else None
        )

    @property
    def mention(
        self
    ):
        return f"<@{self.user_id}>"

# -------------------------------------------------------
#                 PARTICIPANT DISPLAY
# -------------------------------------------------------

    def get_participant_text(
        self
    ):
        if self.initial_wc is None:
            wordcount = "no word count"

        else:
            wordcount = (
                f"{self.initial_wc:,} words"
            )

        project = (
            self.project
            if self.project
            else "no project"
        )

        return (
            f"{self.mention}  ✦  "
            f"{wordcount} ✦  "
            f"**{project}**"
        )


# -------------------------------------------------------
#                  SPRINT PARTICIPANTS
# -------------------------------------------------------

class SprintParticipants:
    def __init__(
        self,
        sprint_id: str
    ):
        self.sprint_id = sprint_id
        self.users = {}

    def add_user(
        self,
        user: discord.User | discord.Member,
        initial_wc=None,
        project=None
    ):
        if user.id in self.users:
            return False

        sprint_user = SprintUser(
            user=user,
            sprint_id=self.sprint_id,
            initial_wc=initial_wc,
            project=project
        )

        self.users[user.id] = sprint_user

        save_previous_sprint_data(
            user_id=user.id,
            initial_wc=initial_wc,
            project=project
        )

        return True

    def remove_user(
        self,
        user_id: int
    ):
        if user_id not in self.users:
            return False

        del self.users[user_id]

        return True

    def has_user(
        self,
        user_id: int
    ):
        return user_id in self.users

    def get_user(
        self,
        user_id: int
    ):
        return self.users.get(
            user_id
        )

    def get_users(
        self
    ):
        return list(
            self.users.values()
        )

    def get_mentions(
        self
    ):
        return [
            sprint_user.mention
            for sprint_user
            in self.users.values()
        ]

    def get_mentions_text(
        self
    ):
        if not self.users:
            return no_participants_message

        return "\n".join(
            sprint_user.get_participant_text()
            for sprint_user
            in self.users.values()
        )

    def get_ping_text(
        self
    ):
        mentions = self.get_mentions()

        if not mentions:
            return None

        return " ".join(
            mentions
        )

    def snapshot(
        self
    ):
        snapshot = SprintParticipants(
            self.sprint_id
        )

        snapshot.users = dict(
            self.users
        )

        return snapshot

    def __len__(
        self
    ):
        return len(
            self.users
        )


# -------------------------------------------------------
#                    JOIN VIEW
# -------------------------------------------------------

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
                join_menu_owner_message,
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="📝 Enter Details",
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
                already_joined_message,
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
        label="↩️ Use Previous",
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
                already_joined_message,
                ephemeral=True
            )

            return

        previous_data = get_previous_sprint_data(
            interaction.user.id
        )

        if previous_data is None:
            await interaction.response.send_message(
                no_previous_data_message,
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
                already_joined_message,
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content=joined_message,
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

        self.initial_wc_input = (
            discord.ui.TextInput(
                label="Initial word count",
                placeholder="e.g. 1932",
                style=discord.TextStyle.short,
                required=False,
                max_length=10
            )
        )

        self.project_input = (
            discord.ui.TextInput(
                label="Project",
                placeholder="e.g. Big Bang 2026",
                style=discord.TextStyle.short,
                required=False,
                max_length=100
            )
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
                join_form_owner_message,
                ephemeral=True
            )

            return

        if self.sprint_view.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                already_joined_message,
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
                    "⚠️ Word count must be a number.",
                    ephemeral=True
                )

                return

            if initial_wc < 0:
                await interaction.response.send_message(
                    "⚠️ Word count cannot be negative.",
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
                already_joined_message,
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            joined_message,
            ephemeral=True
        )

        await self.sprint_view.update_current_message()