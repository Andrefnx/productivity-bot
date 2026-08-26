import discord

from .project_list import (
    create_project,
    create_project_embed,
    get_created_date,
    parse_created_date,
    update_project
)


# -------------------------------------------------------
#                  CREATE PROJECT MODAL
# -------------------------------------------------------

class CreateProjectModal(
    discord.ui.Modal
):
    def __init__(
        self,
        owner_id: int,
        status: str,
        on_created
    ):
        super().__init__(
            title="Create Project"
        )

        self.owner_id = owner_id
        self.status = status

        self.on_created = (
            on_created
        )

        self.name_input = (
            discord.ui.TextInput(
                label="Project name",
                placeholder="e.g. Big Bang 2026",
                required=True,
                max_length=100
            )
        )

        self.description_input = (
            discord.ui.TextInput(
                label="Description",
                placeholder="Optional",
                required=False,
                max_length=300
            )
        )

        self.wordcount_input = (
            discord.ui.TextInput(
                label="Current word count",
                placeholder="e.g. 12500",
                default="0",
                required=True,
                max_length=10
            )
        )

        self.goal_input = (
            discord.ui.TextInput(
                label="Word count goal",
                placeholder="Optional",
                required=False,
                max_length=10
            )
        )

        self.add_item(
            self.name_input
        )

        self.add_item(
            self.description_input
        )

        self.add_item(
            self.wordcount_input
        )

        self.add_item(
            self.goal_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            wordcount = int(
                self.wordcount_input.value
            )

        except ValueError:
            await interaction.response.send_message(
                "Word count must be a number.",
                ephemeral=True
            )

            return

        if wordcount < 0:
            await interaction.response.send_message(
                "Word count cannot be negative.",
                ephemeral=True
            )

            return

        goal = None

        if self.goal_input.value:
            try:
                goal = int(
                    self.goal_input.value
                )

            except ValueError:
                await interaction.response.send_message(
                    "Goal must be a number.",
                    ephemeral=True
                )

                return

            if goal <= 0:
                await interaction.response.send_message(
                    "Goal must be greater than 0.",
                    ephemeral=True
                )

                return

        project = create_project(
            user_id=self.owner_id,
            name=self.name_input.value,
            description=(
                self.description_input.value
            ),
            status=self.status,
            wordcount=wordcount,
            goal=goal
        )

        await self.on_created(
            interaction,
            project
        )


# -------------------------------------------------------
#                  EDIT PROJECT MODAL
# -------------------------------------------------------

class EditProjectModal(
    discord.ui.Modal
):
    def __init__(
        self,
        owner,
        project,
        on_updated
    ):
        super().__init__(
            title="Edit Project"
        )

        self.owner = owner
        self.owner_id = owner.id

        self.project_id = (
            project[
                "project_id"
            ]
        )

        self.on_updated = (
            on_updated
        )

        goal = project.get(
            "goal"
        )

        created = get_created_date(
            project
        )

        self.name_input = (
            discord.ui.TextInput(
                label="Project name",
                default=project.get(
                    "name",
                    ""
                ),
                required=True,
                max_length=100
            )
        )

        self.description_input = (
            discord.ui.TextInput(
                label="Description",
                default=project.get(
                    "description",
                    ""
                ),
                required=False,
                max_length=300
            )
        )

        self.wordcount_input = (
            discord.ui.TextInput(
                label="Current word count",
                default=str(
                    project.get(
                        "wordcount",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.goal_input = (
            discord.ui.TextInput(
                label="Word count goal",
                default=(
                    str(goal)
                    if goal is not None
                    else ""
                ),
                required=False,
                max_length=10
            )
        )

        self.created_input = (
            discord.ui.TextInput(
                label="Created date (DD-MM-YYYY)",
                default=(
                    created
                    if created
                    else ""
                ),
                placeholder="e.g. 01-03-2026",
                required=False,
                max_length=10
            )
        )

        self.add_item(
            self.name_input
        )

        self.add_item(
            self.description_input
        )

        self.add_item(
            self.wordcount_input
        )

        self.add_item(
            self.goal_input
        )

        self.add_item(
            self.created_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            wordcount = int(
                self.wordcount_input.value
            )

        except ValueError:
            await interaction.response.send_message(
                "Word count must be a number.",
                ephemeral=True
            )

            return

        if wordcount < 0:
            await interaction.response.send_message(
                "Word count cannot be negative.",
                ephemeral=True
            )

            return

        goal = None

        if self.goal_input.value:
            try:
                goal = int(
                    self.goal_input.value
                )

            except ValueError:
                await interaction.response.send_message(
                    "Goal must be a number.",
                    ephemeral=True
                )

                return

            if goal <= 0:
                await interaction.response.send_message(
                    "Goal must be greater than 0.",
                    ephemeral=True
                )

                return

        created_at = parse_created_date(
            self.created_input.value
        )

        if created_at is False:
            await interaction.response.send_message(
                (
                    "Created date must use "
                    "DD-MM-YYYY."
                ),
                ephemeral=True
            )

            return

        project = update_project(
            user_id=self.owner_id,
            project_id=self.project_id,
            name=self.name_input.value,
            description=(
                self.description_input.value
            ),
            wordcount=wordcount,
            goal=goal,
            created_at=created_at
        )

        if project is None:
            await interaction.response.send_message(
                "Project not found.",
                ephemeral=True
            )

            return

        await self.on_updated(
            interaction,
            project
        )