import discord

from .config_data import (
    get_user_config,
    update_user_config
)

from .timezone import (
    search_timezones
)


# -------------------------------------------------------
#                    CONFIG EMBED
# -------------------------------------------------------

def create_config_embed(
    user
):
    config = get_user_config(
        user.id
    )

    profile_visibility = (
        "Public"
        if config[
            "profile_visibility"
        ] == "public"
        else "Private"
    )

    projects_visibility = (
        "Public"
        if config[
            "projects_visibility"
        ] == "public"
        else "Private"
    )

    time_format = (
        "12-hour"
        if config[
            "time_format"
        ] == "12h"
        else "24-hour"
    )

    timezone = config.get(
        "timezone",
        "America/Punta_Arenas"
    )

    embed = discord.Embed(
        title="⚙ Settings",
        description=(
            "Manage your privacy and display preferences."
        )
    )

    embed.add_field(
        name="Privacy",
        value=(
            f"Profile ✦ **{profile_visibility}**\n"
            f"Projects ✦ **{projects_visibility}**"
        ),
        inline=False
    )

    embed.add_field(
        name="Date & Time",
        value=(
            f"Time format ✦ **{time_format}**\n"
            f"Timezone ✦ **{timezone}**"
        ),
        inline=False
    )

    return embed


# -------------------------------------------------------
#                  DATE & TIME MODAL
# -------------------------------------------------------

class DateTimeSettingsModal(
    discord.ui.Modal
):
    def __init__(
        self,
        config_view
    ):
        super().__init__(
            title="Date & Time"
        )

        self.config_view = (
            config_view
        )

        config = get_user_config(
            config_view.owner.id
        )

        timezone_input = discord.ui.TextInput(
            default=config.get(
                "timezone",
                "America/Punta_Arenas"
            ),
            placeholder="America/Punta_Arenas",
            required=True,
            max_length=100
        )

        time_format_input = discord.ui.TextInput(
            default=config.get(
                "time_format",
                "12h"
            ),
            placeholder="12h or 24h",
            required=True,
            max_length=3
        )

        self.timezone_input = (
            timezone_input
        )

        self.time_format_input = (
            time_format_input
        )

        self.add_item(
            discord.ui.Label(
                text="Timezone",
                description=(
                    "Use a valid IANA timezone name, "
                    "for example America/Punta_Arenas."
                ),
                component=timezone_input
            )
        )

        self.add_item(
            discord.ui.Label(
                text="Time format",
                description=(
                    "Use 12h or 24h."
                ),
                component=time_format_input
            )
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        timezone_search = (
            self.timezone_input.value
            .strip()
        )

        time_format = (
            self.time_format_input.value
            .strip()
            .lower()
        )

        if time_format not in (
            "12h",
            "24h"
        ):
            await interaction.response.send_message(
                (
                    "Time format must be "
                    "`12h` or `24h`."
                ),
                ephemeral=True
            )

            return

        results = search_timezones(
            timezone_search
        )

        if not results:
            await interaction.response.send_message(
                (
                    "Timezone not found.\n\n"
                    "Try `America/Punta_Arenas`, "
                    "`Punta Arenas`, `Santiago` "
                    "or `Tokyo`."
                ),
                ephemeral=True
            )

            return

        if len(
            results
        ) == 1:
            timezone = results[0]

            update_user_config(
                user_id=(
                    self.config_view.owner.id
                ),
                key="timezone",
                value=timezone
            )

            update_user_config(
                user_id=(
                    self.config_view.owner.id
                ),
                key="time_format",
                value=time_format
            )

            self.config_view.build_components()

            await interaction.response.edit_message(
                embed=create_config_embed(
                    self.config_view.owner
                ),
                view=self.config_view
            )

            return

        view = TimezoneResultsView(
            config_view=self.config_view,
            results=results,
            time_format=time_format,
            search=timezone_search
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Choose Timezone",
                description=(
                    f"Several timezones matched "
                    f"**{timezone_search}**.\n\n"
                    "Choose the correct one below."
                )
            ),
            view=view
        )


# -------------------------------------------------------
#                TIMEZONE RESULT SELECT
# -------------------------------------------------------

class TimezoneResultSelect(
    discord.ui.Select
):
    def __init__(
        self,
        results
    ):
        options = []

        for timezone in results[:25]:
            readable = timezone.replace(
                "_",
                " "
            )

            parts = readable.split(
                "/"
            )

            city = parts[-1]

            region = (
                " / ".join(
                    parts[:-1]
                )
                if len(parts) > 1
                else "Timezone"
            )

            options.append(
                discord.SelectOption(
                    label=city[:100],
                    value=timezone,
                    description=region[:100]
                )
            )

        super().__init__(
            placeholder="Choose your timezone",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        timezone = (
            self.values[0]
        )

        config_view = (
            self.view.config_view
        )

        update_user_config(
            user_id=(
                config_view.owner.id
            ),
            key="timezone",
            value=timezone
        )

        update_user_config(
            user_id=(
                config_view.owner.id
            ),
            key="time_format",
            value=self.view.time_format
        )

        config_view.build_components()

        await interaction.response.edit_message(
            embed=create_config_embed(
                config_view.owner
            ),
            view=config_view
        )


# -------------------------------------------------------
#                TIMEZONE RESULTS VIEW
# -------------------------------------------------------

class TimezoneResultsView(
    discord.ui.View
):
    def __init__(
        self,
        config_view,
        results,
        time_format,
        search
    ):
        super().__init__(
            timeout=120
        )

        self.config_view = (
            config_view
        )

        self.time_format = (
            time_format
        )

        self.search = search

        self.add_item(
            TimezoneResultSelect(
                results
            )
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.config_view.owner.id
        ):
            await interaction.response.send_message(
                (
                    "These settings belong "
                    "to another user."
                ),
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Search Again",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def search_again(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            DateTimeSettingsModal(
                config_view=(
                    self.config_view
                )
            )
        )

    @discord.ui.button(
        label="↩ Back to Settings",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def back_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.config_view.build_components()

        await interaction.response.edit_message(
            embed=create_config_embed(
                self.config_view.owner
            ),
            view=self.config_view
        )


# -------------------------------------------------------
#                     CONFIG VIEW
# -------------------------------------------------------

class ConfigView(
    discord.ui.View
):
    def __init__(
        self,
        owner
    ):
        super().__init__(
            timeout=180
        )

        self.owner = owner

        self.build_components()

    def build_components(
        self
    ):
        self.clear_items()

        config = get_user_config(
            self.owner.id
        )

        profile_private = (
            config[
                "profile_visibility"
            ]
            == "private"
        )

        projects_private = (
            config[
                "projects_visibility"
            ]
            == "private"
        )

        self.profile_privacy.label = (
            "Profile: Private"
            if profile_private
            else "Profile: Public"
        )

        self.projects_privacy.label = (
            "Projects: Private"
            if projects_private
            else "Projects: Public"
        )

        self.add_item(
            self.profile_privacy
        )

        self.add_item(
            self.projects_privacy
        )

        self.add_item(
            self.date_time
        )

        self.add_item(
            self.back_profile
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
                (
                    "These settings belong "
                    "to another user."
                ),
                ephemeral=True
            )

            return False

        return True


# -------------------------------------------------------
#                  PROFILE PRIVACY
# -------------------------------------------------------

    @discord.ui.button(
        label="Profile: Private",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def profile_privacy(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = get_user_config(
            self.owner.id
        )

        current = config[
            "profile_visibility"
        ]

        new_value = (
            "public"
            if current == "private"
            else "private"
        )

        update_user_config(
            user_id=self.owner.id,
            key="profile_visibility",
            value=new_value
        )

        self.build_components()

        await interaction.response.edit_message(
            embed=create_config_embed(
                self.owner
            ),
            view=self
        )


# -------------------------------------------------------
#                 PROJECT PRIVACY
# -------------------------------------------------------

    @discord.ui.button(
        label="Projects: Private",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def projects_privacy(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = get_user_config(
            self.owner.id
        )

        current = config[
            "projects_visibility"
        ]

        new_value = (
            "public"
            if current == "private"
            else "private"
        )

        update_user_config(
            user_id=self.owner.id,
            key="projects_visibility",
            value=new_value
        )

        self.build_components()

        await interaction.response.edit_message(
            embed=create_config_embed(
                self.owner
            ),
            view=self
        )


# -------------------------------------------------------
#                    DATE & TIME
# -------------------------------------------------------

    @discord.ui.button(
        label="Date & Time",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def date_time(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            DateTimeSettingsModal(
                config_view=self
            )
        )


# -------------------------------------------------------
#                  BACK TO PROFILE
# -------------------------------------------------------

    @discord.ui.button(
        label="↩ Back to Profile",
        style=discord.ButtonStyle.primary,
        row=2
    )
    async def back_profile(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        from modules.user_profile.profile import (
            ProfileView,
            create_profile_embed
        )

        await interaction.response.edit_message(
            embed=create_profile_embed(
                self.owner
            ),
            view=ProfileView(
                owner=self.owner
            )
        )