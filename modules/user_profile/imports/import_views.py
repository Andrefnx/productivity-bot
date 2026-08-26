import json

import discord

from .writer_bot import (
    import_writer_bot
)


# -------------------------------------------------------
#                    IMPORT SOURCE
# -------------------------------------------------------

class ImportSourceSelect(
    discord.ui.Select
):
    def __init__(
        self
    ):
        options = [
            discord.SelectOption(
                label="Writer Bot",
                value="writer_bot",
                description=(
                    "Import a Writer Bot JSON export"
                )
            )
        ]

        super().__init__(
            placeholder="Where is the JSON from?",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.source_selected(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                    IMPORT VIEW
# -------------------------------------------------------

class ImportSourceView(
    discord.ui.View
):
    def __init__(
        self,
        owner_id: int
    ):
        super().__init__(
            timeout=120
        )

        self.owner_id = owner_id

        self.add_item(
            ImportSourceSelect()
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner_id
        ):
            await interaction.response.send_message(
                "This import menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def source_selected(
        self,
        interaction,
        source
    ):
        if source == "writer_bot":
            modal = WriterBotImportModal(
                owner_id=self.owner_id
            )

            await interaction.response.send_modal(
                modal
            )


# -------------------------------------------------------
#                 WRITER BOT IMPORT MODAL
# -------------------------------------------------------

class WriterBotImportModal(
    discord.ui.Modal
):
    def __init__(
        self,
        owner_id: int
    ):
        super().__init__(
            title="Import Writer Bot"
        )

        self.owner_id = owner_id

        self.file_upload = (
            discord.ui.FileUpload(
                required=True,
                min_values=1,
                max_values=1
            )
        )

        self.add_item(
            discord.ui.Label(
                text="Writer Bot JSON",
                description=(
                    "Upload the JSON export from Writer Bot."
                ),
                component=self.file_upload
            )
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner_id
        ):
            await interaction.response.send_message(
                "This import belongs to another user.",
                ephemeral=True
            )

            return

        if not self.file_upload.values:
            await interaction.response.send_message(
                "Upload a JSON file.",
                ephemeral=True
            )

            return

        attachment = (
            self.file_upload.values[0]
        )

        filename = (
            attachment.filename.lower()
        )

        if not filename.endswith(
            ".json"
        ):
            await interaction.response.send_message(
                "The file must be a .json file.",
                ephemeral=True
            )

            return

        try:
            raw_data = await attachment.read()

            data = json.loads(
                raw_data.decode(
                    "utf-8-sig"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError
        ):
            await interaction.response.send_message(
                "That file isn't valid JSON.",
                ephemeral=True
            )

            return

        try:
            result = import_writer_bot(
                user_id=interaction.user.id,
                data=data
            )

        except ValueError as error:
            await interaction.response.send_message(
                str(error),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            (
                "**Writer Bot import complete.**\n\n"
                f"Projects imported: **{result['total']}**\n"
                f"New projects: **{result['created']}**\n"
                f"Updated projects: **{result['updated']}**\n\n"

            ),
            ephemeral=True
        )