import uuid

import discord

from modules.user_profile.profile import (
    set_last_project
)

from modules.user_profile.projects import (
    ProjectPickerView,
    create_project_picker_embed,
    update_project
)


# -------------------------------------------------------
#                     SPRINT USER
# -------------------------------------------------------

class SprintUser:
    def __init__(
        self,
        user,
        sprint_id: str,
        project
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

        self.accumulated_words = 0

        self.result_registered = False

        self.activity_history = []

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
        ):
            update_project(
                user_id=self.user_id,
                project_id=self.project_id,
                wordcount=final_wc
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
        project
    ):
        if user.id in self.users:
            return False

        sprint_user = SprintUser(
            user=user,
            sprint_id=self.sprint_id,
            project=project
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

    async def join_project(
        self,
        interaction,
        project
    ):
        if self.sprint_view.participants.has_user(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        added = (
            self.sprint_view.participants.add_user(
                user=interaction.user,
                project=project
            )
        )

        if not added:
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Joined sprint",
                description=(
                    f"**{project['name']}** ✦ "
                    f"{project.get('wordcount', 0):,} words"
                )
            ),
            view=None
        )

        await self.sprint_view.update_current_message()