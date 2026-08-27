import discord

from .help_messages import (
    GETTING_STARTED_DESCRIPTION,
    GETTING_STARTED_TITLE,
    HELP_HOME_DESCRIPTION,
    HELP_HOME_TITLE,
    IMPORTS_DESCRIPTION,
    IMPORTS_TITLE,
    PROFILE_DESCRIPTION,
    PROFILE_TITLE,
    PROJECTS_DESCRIPTION,
    PROJECTS_TITLE,
    SETTINGS_DESCRIPTION,
    SETTINGS_TITLE,
    SPRINTS_DESCRIPTION,
    SPRINTS_TITLE
)


# -------------------------------------------------------
#                     HELP EMBEDS
# -------------------------------------------------------

def create_help_embed():
    return discord.Embed(
        title=HELP_HOME_TITLE,
        description=HELP_HOME_DESCRIPTION
    )


def create_section_embed(
    title,
    description
):
    return discord.Embed(
        title=title,
        description=description
    )


# -------------------------------------------------------
#                     HELP SELECT
# -------------------------------------------------------

class HelpSelect(
    discord.ui.Select
):
    def __init__(
        self
    ):
        options = [
            discord.SelectOption(
                label="Getting Started",
                value="getting_started",
                description="Commands and basic navigation"
            ),
            discord.SelectOption(
                label="Sprints",
                value="sprints",
                description="Joining, progress and results"
            ),
            discord.SelectOption(
                label="Projects",
                value="projects",
                description="Create, edit and organize projects"
            ),
            discord.SelectOption(
                label="Profile",
                value="profile",
                description="Your personal bot menu"
            ),
            discord.SelectOption(
                label="Settings",
                value="settings",
                description="Privacy, timezone and preferences"
            ),
            discord.SelectOption(
                label="Imports",
                value="imports",
                description="Import data from other bots"
            )
        ]

        super().__init__(
            placeholder="Choose a help topic",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.open_section(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                      HELP VIEW
# -------------------------------------------------------

class HelpView(
    discord.ui.View
):
    def __init__(
        self,
        owner
    ):
        super().__init__(
            timeout=300
        )

        self.owner = owner

        self.add_item(
            HelpSelect()
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner.id
        ):
            await interaction.response.send_message(
                "Open `/help` to use your own help menu.",
                ephemeral=True
            )

            return False

        return True

    async def open_section(
        self,
        interaction,
        section
    ):
        sections = {
            "getting_started": (
                GETTING_STARTED_TITLE,
                GETTING_STARTED_DESCRIPTION
            ),
            "sprints": (
                SPRINTS_TITLE,
                SPRINTS_DESCRIPTION
            ),
            "projects": (
                PROJECTS_TITLE,
                PROJECTS_DESCRIPTION
            ),
            "profile": (
                PROFILE_TITLE,
                PROFILE_DESCRIPTION
            ),
            "settings": (
                SETTINGS_TITLE,
                SETTINGS_DESCRIPTION
            ),
            "imports": (
                IMPORTS_TITLE,
                IMPORTS_DESCRIPTION
            )
        }

        section_data = sections.get(
            section
        )

        if section_data is None:
            await interaction.response.send_message(
                "Help section not found.",
                ephemeral=True
            )

            return

        title, description = (
            section_data
        )

        await interaction.response.edit_message(
            embed=create_section_embed(
                title,
                description
            ),
            view=self
        )


# -------------------------------------------------------
#                    HELP HOME BUTTON
# -------------------------------------------------------

    @discord.ui.button(
        label="↩ Back to Help",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def back_home(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            embed=create_help_embed(),
            view=self
        )