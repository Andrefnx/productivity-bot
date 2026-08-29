import discord

from .sprint_config import (
	create_sprint_config,
	set_sprint_override
)

from ..permissions import can_edit_sprint_settings


# -------------------------------------------------------
#                   SPRINT SETTINGS VIEW
# -------------------------------------------------------

class SprintConfigView(
	discord.ui.View
):
	def __init__(
		self,
		overrides=None
	):
		super().__init__(
			timeout=180
		)
		self.sprint_view = None
		self.config = create_sprint_config(
			overrides
		)

	def get_overrides(self):
		return self.config.copy()


# -------------------------------------------------------
#                   SPRINT SETTINGS EMBED
# -------------------------------------------------------

SPRINT_SETTING_LABELS = {
	"allow_join_after_start": "Join after start",
	"allow_leave_after_start": "Leave after start",
	"allow_change_duration_after_start": "Change duration after start",
	"allow_change_waiting_time": "Change waiting time",
	"empty_sprint_timeout": "Empty sprint timeout"
}


def create_sprint_settings_embed(
	sprint_view,
	config=None
):
	embed = discord.Embed(
		title="Sprint Settings / Edit Settings",
		description="Overrides apply only to this sprint session."
	)

	shown_config = sprint_view.sprint_config if config is None else config

	for key, value in shown_config.items():
		shown_value = (
			"Inherit"
			if value is None
			else "Allowed"
			if value is True
			else "Disabled"
			if value is False
			else f"{value} seconds"
		)
		embed.add_field(
			name=SPRINT_SETTING_LABELS[key],
			value=shown_value,
			inline=False
		)

	return embed


# -------------------------------------------------------
#                   SPRINT SETTINGS SELECT
# -------------------------------------------------------

class SprintSettingSelect(
	discord.ui.Select
):
	def __init__(
		self,
		settings_view,
		key,
		row
	):
		self.settings_view = settings_view
		self.key = key
		options = [
			discord.SelectOption(label="Inherit", value="inherit"),
			discord.SelectOption(label="Allowed", value="allowed"),
			discord.SelectOption(label="Disabled", value="disabled")
		]

		if key == "empty_sprint_timeout":
			options = [
				discord.SelectOption(label="Inherit", value="inherit"),
				discord.SelectOption(label="30 seconds", value="30"),
				discord.SelectOption(label="60 seconds", value="60"),
				discord.SelectOption(label="120 seconds", value="120")
			]

		super().__init__(
			placeholder=SPRINT_SETTING_LABELS[key],
			options=options,
			row=row
		)

	async def callback(
		self,
		interaction: discord.Interaction
	):
		value = self.values[0]
		if value == "inherit":
			value = None
		elif self.key != "empty_sprint_timeout":
			value = value == "allowed"
		else:
			value = int(value)

		set_sprint_override(
			self.settings_view.draft_config,
			self.key,
			value
		)

		await interaction.response.edit_message(
			embed=create_sprint_settings_embed(
				self.settings_view.sprint_view,
				self.settings_view.draft_config
			),
			view=self.settings_view
		)


# -------------------------------------------------------
#                   SPRINT SETTINGS VIEW
# -------------------------------------------------------

class SprintSettingsView(
	discord.ui.View
):
	def __init__(
		self,
		sprint_view,
		back_view=None
	):
		super().__init__(
			timeout=120
		)
		self.sprint_view = sprint_view
		self.back_view = back_view
		self.draft_config = create_sprint_config(
			sprint_view.sprint_config
		)

		for row, key in enumerate(
			self.draft_config
		):
			self.add_item(
				SprintSettingSelect(
					self,
					key,
					row
				)
			)

		self.add_item(SaveSprintSettingsButton(self))
		self.add_item(BackSprintSettingsButton(self))

	async def interaction_check(
		self,
		interaction: discord.Interaction
	):
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
			row=4
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
			row=4
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
