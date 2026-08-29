import discord

from modules.config.permissions import can_edit_sprint_settings
from modules.config.sprint.sprint_config import (
    create_sprint_config,
    set_sprint_override
)


SPRINT_SETTING_LABELS = {
    "allow_join_after_start": "Join after start",
    "allow_leave_after_start": "Leave after start",
    "allow_change_duration_after_start": "Change duration after start",
    "allow_change_waiting_time": "Change waiting time",
    "empty_sprint_timeout": "Empty sprint timeout"
}

BOOLEAN_SETTING_VALUES = (
    ("Inherit", "inherit"),
    ("Allowed", "allowed"),
    ("Disabled", "disabled")
)

TIMEOUT_SETTING_VALUES = (
    ("Inherit", "inherit"),
    ("30 seconds", "30"),
    ("60 seconds", "60"),
    ("120 seconds", "120")
)


class SprintConfigView(discord.ui.View):
    def __init__(self, overrides=None):
        super().__init__(timeout=180)
        self.sprint_view = None
        self.config = create_sprint_config(overrides)

    def get_overrides(self):
        return self.config.copy()


def format_sprint_setting_value(value):
    if value is None:
        return "Inherit"
    if value is True:
        return "Allowed"
    if value is False:
        return "Disabled"
    return f"{value} seconds"


def create_sprint_settings_embed(sprint_view, config=None):
    shown_config = sprint_view.sprint_config if config is None else config

    embed = discord.Embed(
        title="Sprint Settings / Edit Settings",
        description=(
            "Choose changes below, then press **Save**. "
            "Use **↩ Back** to discard unsaved changes."
        )
    )

    for key, value in shown_config.items():
        embed.add_field(
            name=SPRINT_SETTING_LABELS[key],
            value=format_sprint_setting_value(value),
            inline=False
        )

    return embed


class SprintSettingSelect(discord.ui.Select):
    def __init__(self, settings_view):
        self.settings_view = settings_view
        options = []

        for key, label in SPRINT_SETTING_LABELS.items():
            values = (
                TIMEOUT_SETTING_VALUES
                if key == "empty_sprint_timeout"
                else BOOLEAN_SETTING_VALUES
            )

            for shown_value, stored_value in values:
                options.append(
                    discord.SelectOption(
                        label=f"{label}: {shown_value}"[:100],
                        value=f"{key}|{stored_value}",
                        description=(
                            "Current: "
                            + format_sprint_setting_value(
                                settings_view.draft_config.get(key)
                            )
                        )[:100]
                    )
                )

        super().__init__(
            placeholder="Change a sprint setting",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        key, raw_value = self.values[0].split("|", 1)

        if raw_value == "inherit":
            value = None
        elif key == "empty_sprint_timeout":
            value = int(raw_value)
        else:
            value = raw_value == "allowed"

        set_sprint_override(
            self.settings_view.draft_config,
            key,
            value
        )

        self.settings_view.refresh_components()

        await interaction.response.edit_message(
            embed=create_sprint_settings_embed(
                self.settings_view.sprint_view,
                self.settings_view.draft_config
            ),
            view=self.settings_view
        )


class SprintSettingsView(discord.ui.View):
    def __init__(self, sprint_view, back_view=None):
        super().__init__(timeout=120)
        self.sprint_view = sprint_view
        self.back_view = back_view
        self.draft_config = create_sprint_config(sprint_view.sprint_config)
        self.refresh_components()

    def refresh_components(self):
        self.clear_items()
        self.add_item(SprintSettingSelect(self))
        self.add_item(SaveSprintSettingsButton(self))
        self.add_item(BackSprintSettingsButton(self))

    async def interaction_check(self, interaction: discord.Interaction):
        if not can_edit_sprint_settings(
            interaction.user,
            self.sprint_view.creator_id
        ):
            await interaction.response.send_message(
                "Only the sprint creator or moderators can edit these settings.",
                ephemeral=True
            )
            return False

        return True


class SaveSprintSettingsButton(discord.ui.Button):
    def __init__(self, settings_view):
        self.settings_view = settings_view
        super().__init__(
            label="Save",
            style=discord.ButtonStyle.primary,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        self.settings_view.sprint_view.sprint_config.clear()
        self.settings_view.sprint_view.sprint_config.update(
            self.settings_view.draft_config
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Sprint Settings",
                description="Settings saved. Choose an action."
            ),
            view=self.settings_view.back_view
        )
        self.settings_view.stop()


class BackSprintSettingsButton(discord.ui.Button):
    def __init__(self, settings_view):
        self.settings_view = settings_view
        super().__init__(
            label="↩ Back",
            style=discord.ButtonStyle.secondary,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Sprint Settings",
                description="Choose an action."
            ),
            view=self.settings_view.back_view
        )
        self.settings_view.stop()
