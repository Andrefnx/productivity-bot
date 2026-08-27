import discord

from ..validation import validate_word_count_change


# -------------------------------------------------------
#                 WORD COUNT CHANGE MODAL
# -------------------------------------------------------

class WordCountChangeModal(
    discord.ui.Modal
):
    def __init__(
        self,
        initial_total: int,
        on_validated,
        title="Register Word Count"
    ):
        super().__init__(
            title=title
        )

        self.initial_total = initial_total
        self.on_validated = on_validated

        self.new_total_input = discord.ui.TextInput(
            label="OPTION 1 — New total word count",
            placeholder="Choose this OR the option below",
            required=False,
            max_length=10
        )

        self.difference_input = discord.ui.TextInput(
            label="OPTION 2 — Words added or removed",
            placeholder="Choose this OR the option above",
            required=False,
            max_length=10
        )

        self.add_item(
            self.new_total_input
        )
        self.add_item(
            self.difference_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        result, error = validate_word_count_change(
            self.new_total_input.value,
            self.difference_input.value,
            self.initial_total
        )

        if error:
            await interaction.response.send_message(
                error,
                ephemeral=True
            )
            return

        await self.on_validated(
            interaction,
            result
        )
