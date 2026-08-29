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
        self.sprint_user_id = f"{sprint_id}:{user.id}"
        self.session_id = str(uuid.uuid4())
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
    def mention(self):
        return f"<@{self.user_id}>"

    def set_last_project(self):
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

        if registered and words_written is not None:
            self.accumulated_words += words_written

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

    def switch_project(self, project, initial_wc=None):
        self.project_id = project.get("project_id") if project else None
        self.project = project.get("name", "Untitled") if project else "No project"

        if initial_wc is None:
            initial_wc = int(project.get("wordcount", 0)) if project else 0

        self.initial_wc = initial_wc
        self.final_wc = None
        self.words_written = None
        self.result_registered = False

        if self.project_id is not None:
            self.set_last_project()

    def get_participant_text(self):
        return (
            f"{self.mention} ✦ "
            f"{self.initial_wc:,} words ✦ "
            f"**{self.project}**"
        )


# -------------------------------------------------------
#                  SPRINT PARTICIPANTS
# -------------------------------------------------------

class SprintParticipants:
    def __init__(self, sprint_id: str):
        self.sprint_id = sprint_id
        self.users = {}

    def add_user(self, user, project=None, initial_wc=0):
        if user.id in self.users:
            return False

        self.users[user.id] = SprintUser(
            user=user,
            sprint_id=self.sprint_id,
            project=project,
            initial_wc=initial_wc
        )
        return True

    def remove_user(self, user_id: int):
        if user_id not in self.users:
            return False
        del self.users[user_id]
        return True

    def has_user(self, user_id: int):
        return user_id in self.users

    def get_user(self, user_id: int):
        return self.users.get(user_id)

    def get_users(self):
        return list(self.users.values())

    def get_mentions(self):
        return [sprint_user.mention for sprint_user in self.users.values()]

    def get_mentions_text(self):
        if not self.users:
            return "No participants yet."
        return "\n".join(
            sprint_user.get_participant_text()
            for sprint_user in self.users.values()
        )

    def get_ping_text(self):
        mentions = self.get_mentions()
        if not mentions:
            return None
        return " ".join(mentions)

    def snapshot(self):
        snapshot = SprintParticipants(self.sprint_id)
        snapshot.users = dict(self.users)
        return snapshot

    def __len__(self):
        return len(self.users)


# -------------------------------------------------------
#              REUSABLE ACTIVITY SELECTION FLOW
# -------------------------------------------------------

def create_start_word_count_embed(project):
    if project is None:
        description = "Choose **Custom** to start from 0 or another value."
    else:
        description = (
            f"**{project['name']}**\n"
            "Choose **Total** to use the project total, or "
            "**Custom** to start from 0 or another value."
        )

    return discord.Embed(
        title="Starting Word Count",
        description=description
    )


class SprintActivityPickerView(ProjectPickerView):
    def __init__(
        self,
        owner_id: int,
        on_activity_confirm,
        back_callback=None,
        show_last_project=True
    ):
        self.on_activity_confirm = on_activity_confirm
        self.back_callback = back_callback

        super().__init__(
            owner_id=owner_id,
            on_confirm=self.project_selected,
            show_last_project=show_last_project
        )
        self.add_item(self.no_project)

        if self.back_callback is not None:
            self.add_item(ActivityPickerBackButton(self))

    async def project_selected(self, interaction, project):
        await self.open_word_count(interaction, project)

    async def open_word_count(self, interaction, project):
        await interaction.response.edit_message(
            content=None,
            embed=create_start_word_count_embed(project),
            view=StartWordCountView(
                owner_id=self.owner_id,
                project=project,
                on_confirm=self.on_activity_confirm,
                back_callback=self.return_to_picker
            )
        )

    async def return_to_picker(self, interaction):
        await interaction.response.edit_message(
            content=None,
            embed=create_project_picker_embed(),
            view=SprintActivityPickerView(
                owner_id=self.owner_id,
                on_activity_confirm=self.on_activity_confirm,
                back_callback=self.back_callback,
                show_last_project=self.show_last_project
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
        await self.open_word_count(interaction, None)


class ActivityPickerBackButton(discord.ui.Button):
    def __init__(self, picker_view):
        self.picker_view = picker_view
        super().__init__(
            label="↩ Back",
            style=discord.ButtonStyle.secondary,
            row=4
        )

    async def callback(self, interaction: discord.Interaction):
        await self.picker_view.back_callback(interaction)


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

        await self.start_view.confirm_activity(interaction, initial_wc)


class StartWordCountView(discord.ui.View):
    def __init__(
        self,
        owner_id,
        project,
        on_confirm,
        back_callback
    ):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.project = project
        self.on_confirm = on_confirm
        self.back_callback = back_callback

        if project is None:
            self.remove_item(self.total)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This menu belongs to another user.",
                ephemeral=True
            )
            return False
        return True

    async def confirm_activity(self, interaction, initial_wc):
        await self.on_confirm(
            interaction,
            self.project,
            initial_wc
        )

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
        await self.confirm_activity(
            interaction,
            int(self.project.get("wordcount", 0))
        )

    @discord.ui.button(
        label="↩ Back",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def back(self, interaction, button):
        await self.back_callback(interaction)


# -------------------------------------------------------
#                    JOIN VIEW
# -------------------------------------------------------

class JoinSprintView(SprintActivityPickerView):
    def __init__(self, sprint_view, user_id: int):
        self.sprint_view = sprint_view
        super().__init__(
            owner_id=user_id,
            on_activity_confirm=self.finish_join,
            show_last_project=True
        )

    async def finish_join(self, interaction, project, initial_wc):
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

        if self.sprint_view.participants.has_user(interaction.user.id):
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )
            return

        added = self.sprint_view.participants.add_user(
            user=interaction.user,
            project=project,
            initial_wc=initial_wc
        )

        if not added:
            await interaction.response.send_message(
                "You are already in this sprint.",
                ephemeral=True
            )
            return

        self.sprint_view.participant_joined()

        project_name = project.get("name") if project else "No project"
        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Joined sprint",
                description=f"**{project_name}** ✦ {initial_wc:,} words"
            ),
            view=None
        )

        await self.sprint_view.update_current_message()
