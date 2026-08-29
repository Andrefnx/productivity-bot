import uuid

import discord

from modules.config import resolve_sprint_setting

from modules.user_profile.profile import (
    set_last_project
)

from modules.user_profile.projects import (
    ProjectPickerView,
    create_project_picker_embed,
    add_project_words
)


# -------------------------------------------------------
#                     SPRINT USER
# -------------------------------------------------------

class SprintUser:
    def __init__(
        self,
        user,
        sprint_id: str,
        project=None,
        initial_wc=0
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

        self.project_id = project.get("project_id") if project else None
        self.project = project.get("name", "Untitled") if project else "No project"
        self.initial_wc = initial_wc

        self.final_wc = None
        self.words_written = None

        self.accumulated_words = 0

        self.result_registered = False

        self.activity_history = []

        if self.project_id is not None:
            self.set_last_project()

    @property
    def mention(
        self
    ):
        return f"<@{self.user_id}>"

    def set_last_project(
        self
    ):
        set_last_project(
            user_id=self.user_id,
            project_id=self.project_id
        )

    def archive_activity(
        self,
        final_wc=None,
        words_written=None,
        registered=False
    ):
        self.activity_history.append(
            {
                "project_id": self.project_id,
                "project": self.project,
                "initial_wc": self.initial_wc,
                "final_wc": final_wc,
                "words_written": words_written,
                "registered": registered
            }
        )

        if (
            registered
            and words_written is not None
        ):
            self.accumulated_words += (
                words_written
            )

        if (
            registered
            and final_wc is not None
            and self.project_id is not None
        ):
            add_project_words(
                user_id=self.user_id,
                project_id=self.project_id,
                words=max(words_written or 0, 0)
            )

    def switch_project(
        self,
        project
    ):
        self.project_id = (
            project[
                "project_id"
            ]
        )

        self.project = (
            project.get(
                "name",
                "Untitled"
            )
        )

        self.initial_wc = (
            project.get(
                "wordcount",
                0
            )
        )

        self.final_wc = None
        self.words_written = None

        self.result_registered = False

        self.set_last_project()

    def get_participant_text(
        self
    ):
        return (
            f"{self.mention} ✦ "
            f"{self.initial_wc:,} words ✦ "
            f"**{self.project}**"
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
        user,
        project=None,
        initial_wc=0
    ):
        if user.id in self.users:
            return False

        sprint_user = SprintUser(
            user=user,
            sprint_id=self.sprint_id,
            project=project,
            initial_wc=initial_wc
        )

        self.users[
            user.id
        ] = sprint_user

        return True

    def remove_user(
        self,
        user_id: int
    ):
        if user_id not in self.users:
            return False

        del self.users[
            user_id
        ]

        return True

    def has_user(
        self,
        user_id: int
    ):
        return (
            user_id
            in self.users
        )

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
            return "No participants yet."

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
    ProjectPickerView
):
    def __init__(
        self,
        sprint_view,
        user_id: int
    ):
        self.sprint_view = sprint_view

        super().__init__(
            owner_id=user_id,
            on_confirm=self.join_project,
            show_last_project=True
        )
        self.add_item(self.no_project)

    async def join_project(
        self,
        interaction,
        project
    ):
        if self.sprint_view.started and not resolve_sprint_setting(
            "allow_join_after_start",
            self.sprint_view.channel_config,
            self.sprint_view.sprint_config
        ):
            await interaction.response.send_message(
                "Joining after the sprint starts is disabled.",
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

        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Starting Word Count",
                description=(
                    f"**{project['name']}**\n"
                    "Choose **Total** to use the project total, or "
                    "**Custom** to start from 0 or another value."
                )
            ),
            view=StartWordCountView(
                sprint_view=self.sprint_view,
                user_id=interaction.user.id,
                project=project
            )
        )

    @discord.ui.button(
        label="No Project",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def no_project(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Starting Word Count",
                description=(
                    "Choose **Custom** to start from 0 or another value."
                )
            ),
            view=StartWordCountView(
                sprint_view=self.sprint_view,
                user_id=interaction.user.id,
                project=None
            )
        )


class StartWordCountModal(discord.ui.Modal):
    def __init__(self, start_view):
        super().__init__(title="Custom Starting Word Count")
        self.start_view = start_view
        self.wordcount_input = discord.ui.TextInput(
            label="Starting word count",
            default="0",
            required=True,
            max_length=12
        )
        self.add_item(self.wordcount_input)

    async def on_submit(self, interaction):
        try:
            initial_wc = int(self.wordcount_input.value.strip())
            if initial_wc < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Starting word count must be a whole number of 0 or more.",
                ephemeral=True
            )
            return

        await self.start_view.add_participant(interaction, initial_wc)


class StartWordCountView(discord.ui.View):
    def __init__(self, sprint_view, user_id, project):
        super().__init__(timeout=120)
        self.sprint_view = sprint_view
        self.user_id = user_id
        self.project = project

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This join menu belongs to another user.",
                ephemeral=True
            )
            return False
        return True

    async def add_participant(self, interaction, initial_wc):
        if self.sprint_view.participants.has_user(interaction.user.id):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )
            return

        added = self.sprint_view.participants.add_user(
            user=interaction.user,
            project=self.project,
            initial_wc=initial_wc
        )

        if not added:
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        project_name = self.project.get("name") if self.project else "No project"
        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Joined sprint",
                description=(
                    f"**{project_name}** ✦ {initial_wc:,} words"
                )
            ),
            view=None
        )

        await self.sprint_view.update_current_message()

    @discord.ui.button(
        label="Custom",
        style=discord.ButtonStyle.secondary
    )
    async def custom(self, interaction, button):
        await interaction.response.send_modal(StartWordCountModal(self))

    @discord.ui.button(
        label="Total",
        style=discord.ButtonStyle.secondary
    )
    async def total(self, interaction, button):
        if self.project is None:
            await interaction.response.send_message(
                "Total is only available when you select a project.",
                ephemeral=True
            )
            return

        await self.add_participant(
            interaction,
            int(self.project.get("wordcount", 0))
        )