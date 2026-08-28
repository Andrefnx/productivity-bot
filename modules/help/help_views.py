import discord

from .help_messages import (
    HELP_HOME_DESCRIPTION,
    HELP_HOME_TITLE
)

from modules.ui_registry import get_help_registry


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
        self,
        guild_id
    ):
        registry = get_help_registry()
        options = [
            discord.SelectOption(
                label=entry.label,
                value=entry.key,
                description=entry.description
            )
            for entry in registry.entries(guild_id=guild_id)
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
        owner,
        guild_id=None
    ):
        super().__init__(
            timeout=300
        )

        self.owner = owner
        self.guild_id = guild_id

        self.add_item(
            HelpSelect(guild_id)
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
        registry = get_help_registry()
        entry = registry.get(section)

        if entry not in registry.entries(
            guild_id=interaction.guild_id
        ):
            await interaction.response.send_message(
                "Help section not found.",
                ephemeral=True
            )

            return

        title, description = entry.renderer()

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