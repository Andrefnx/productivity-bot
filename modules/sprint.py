import discord


class SprintView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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
        await interaction.response.send_message(
            "You joined the sprint!",
            ephemeral=True
        )

    @discord.ui.button(
        label="Leave",
        style=discord.ButtonStyle.danger,
        row=0
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "You left the sprint!",
            ephemeral=True
        )

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
        await interaction.response.send_message(
            "Sprint cancelled!",
            ephemeral=True
        )

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
        await interaction.response.send_message(
            "Sprint time editing is coming soon!",
            ephemeral=True
        )

    @discord.ui.button(
        label="Change Projects",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def change_projects(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Project selection is coming soon!",
            ephemeral=True
        )

class SprintCreateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create a Writing Sprint")

        self.duration_input = discord.ui.TextInput(
        label="Duration (minutes)",
        placeholder="e.g. 30",
        required=True,
        max_length=4
)

        self.starts_in_input = discord.ui.TextInput(
            label="Starts in (minutes)",
            placeholder="e.g. 10",
            style=discord.TextStyle.short,
            required=True,
            max_length=4
        )

        self.add_item(self.duration_input)
        self.add_item(self.starts_in_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration = int(self.duration_input.value)
            starts_in = int(self.starts_in_input.value)
        except ValueError:
            await interaction.response.send_message(
                "Duration and start time must be numbers.",
                ephemeral=True
            )
            return

        if duration <= 0 or starts_in < 0:
            await interaction.response.send_message(
                "Duration must be greater than 0, and start time cannot be negative.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Writing Sprint",
            description="A writing sprint has been created!"
        )

        embed.add_field(
            name="Duration",
            value=f"{duration} minutes",
            inline=True
        )

        embed.add_field(
            name="Starts in",
            value=f"{starts_in} minutes",
            inline=True
        )

        embed.add_field(
            name="Participants",
            value="0",
            inline=False
        )

        view = SprintView()

        await interaction.response.send_message(
            embed=embed,
            view=view
        )