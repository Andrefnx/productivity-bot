import discord

from .channel_config import (
	get_channel_config,
	update_channel_config
)

from ..permissions import can_edit_channel_config


# -------------------------------------------------------
#                  CHANNEL SETTINGS EMBED
# -------------------------------------------------------

SETTING_DESCRIPTIONS = {
	"create_sprints": "Who may create sprints.",
	"cancel_sprints": "Who may cancel an active sprint.",
	"change_sprint_time": "Who may change sprint timing.",
	"allow_join_after_start": "Allow joining after a sprint starts.",
	"allow_leave_after_start": "Allow leaving after a sprint starts.",
	"allow_change_duration_after_start": "Allow duration changes after start.",
	"allow_change_waiting_time": "Allow waiting-time changes.",
	"default_duration": "Duration used when a sprint starts.",
	"min_duration": "Shortest permitted sprint duration.",
	"max_duration": "Longest permitted sprint duration.",
	"start_waiting_time": "Time before a sprint starts.",
	"word_count_waiting_time": "Time available to register word count after a sprint.",
	"cancel_empty_sprints": "Cancel a sprint when nobody joins.",
	"empty_sprint_timeout": "Minutes to wait before cancelling an empty sprint."
}

SETTING_GROUPS = [
	(
		"Sprint Permissions",
		(
			"create_sprints",
			"cancel_sprints",
			"change_sprint_time"
		)
	),
	(
		"Sprint Behavior",
		(
			"allow_join_after_start",
			"allow_leave_after_start",
			"allow_change_duration_after_start",
			"allow_change_waiting_time"
		)
	),
	(
		"Timing",
		(
			"default_duration",
			"min_duration",
			"max_duration",
			"start_waiting_time",
			"word_count_waiting_time"
		)
	),
	(
		"Empty Sprints",
		(
			"cancel_empty_sprints",
			"empty_sprint_timeout"
		)
	)
]


def create_channel_config_embed(
	guild_id,
	channel_id,
	page=0
):
	config = get_channel_config(
		guild_id,
		channel_id
	)

	group_name, group_keys = SETTING_GROUPS[
		page
	]

	embed = discord.Embed(
		title=f"Channel Settings • {group_name}"
	)

	for key in group_keys:
		value = config[key]
		embed.add_field(
			name=key.replace(
				"_",
				" "
			).title(),
			value=f"`{value}`",
			inline=False
		)

	return embed


# -------------------------------------------------------
#                  CHANNEL SETTINGS MODALS
# -------------------------------------------------------

class ChannelSettingsModal(
	discord.ui.Modal
):
	def __init__(
		self,
		view,
		title,
		fields
	):
		super().__init__(
			title=title
		)
		self.config_view = view
		self.fields = {}

		for key, description in fields:
			field = discord.ui.TextInput(
				default=str(
					view.config[key]
				),
				required=True,
				max_length=50
			)
			self.fields[key] = field
			self.add_item(
				discord.ui.Label(
					text=key.replace(
						"_",
						" "
					).title(),
					description=description,
					component=field
				)
			)

	async def on_submit(
		self,
		interaction: discord.Interaction
	):
		try:
			for key, field in self.fields.items():
				value = field.value.strip()
				current = self.config_view.config[key]

				if isinstance(current, bool):
					value = value.lower()
					if value not in ("true", "false"):
						raise ValueError
					value = value == "true"
				elif isinstance(current, int):
					value = int(value)
					if value < 0:
						raise ValueError
				elif key in (
					"create_sprints"
				):
					if value not in (
						"everyone",
						"manage_messages",
						"admin"
					):
						raise ValueError
				elif key in (
					"cancel_sprints",
					"change_sprint_time"
				):
					if value not in (
						"creator",
						"creator_or_moderator",
						"admin"
					):
						raise ValueError

				update_channel_config(
					self.config_view.guild_id,
					self.config_view.channel_id,
					key,
					value
				)
		except ValueError:
			await interaction.response.send_message(
				"Use valid values for every setting.",
				ephemeral=True
			)
			return

		self.config_view.refresh()
		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.config_view.guild_id,
				self.config_view.channel_id,
				self.config_view.page
			),
			view=self.config_view
		)


# -------------------------------------------------------
#                 CHANNEL VALUE OPTIONS
# -------------------------------------------------------

def get_setting_options(
	key,
	current_value
):
	if key == "create_sprints":
		return [
			("Everyone", "everyone", "All members can create sprints."),
			("Members with Manage Messages", "manage_messages", "Members with Manage Messages can create sprints."),
			("Administrators", "admin", "Only server administrators can create sprints.")
		]

	if key in (
		"cancel_sprints",
		"change_sprint_time"
	):
		return [
			("Sprint Creator", "creator", "Only the member who created the sprint."),
			("Creator or Moderators", "creator_or_moderator", "The creator or members with moderation permissions."),
			("Administrators", "admin", "Only server administrators.")
		]

	if isinstance(current_value, bool):
		return [
			("Enabled", "true", "Allow this action in the channel."),
			("Disabled", "false", "Disable this action in the channel.")
		]

	numeric_options = {
		"default_duration": (1, 5, 10, 15, 30, 60, 90, 120, 180),
		"min_duration": (1, 5, 10, 15, 30),
		"max_duration": (30, 60, 90, 120, 180),
		"start_waiting_time": (0, 1, 2, 5, 10, 15, 30, 60),
		"word_count_waiting_time": (1, 2, 5, 10, 15, 30, 60),
		"empty_sprint_timeout": (1, 2, 5, 10, 15, 30, 60)
	}

	return [
		(
			f"{value} minutes",
			str(value),
			f"Use {value} minutes for this channel setting."
		)
		for value in numeric_options[key]
	]


def validate_channel_config(
	config
):
	if config["min_duration"] > config["max_duration"]:
		return "Minimum duration cannot be greater than maximum duration."

	if not (
		config["min_duration"]
		<= config["default_duration"]
		<= config["max_duration"]
	):
		return "Default duration must be between the minimum and maximum duration."

	if config["empty_sprint_timeout"] <= 0:
		return "Empty sprint timeout must be positive."

	return None


# -------------------------------------------------------
#                 CHANNEL SETTING SELECTS
# -------------------------------------------------------

class ChannelSettingSelect(
	discord.ui.Select
):
	def __init__(
		self,
		edit_view
	):
		self.edit_view = edit_view
		_, group_keys = SETTING_GROUPS[
			edit_view.page
		]

		super().__init__(
			placeholder="Select a channel setting",
			options=[
				discord.SelectOption(
					label=key.replace("_", " ").title(),
					value=key,
					default=(key == edit_view.setting_key)
				)
				for key in group_keys
			],
			row=0
		)

	async def callback(
		self,
		interaction: discord.Interaction
	):
		self.edit_view.setting_key = self.values[0]
		self.edit_view.pending_value = str(
			self.edit_view.config[
				self.edit_view.setting_key
			]
		)
		self.edit_view.refresh_components()
		await interaction.response.edit_message(
			embed=self.edit_view.create_embed(),
			view=self.edit_view
		)


class ChannelValueSelect(
	discord.ui.Select
):
	def __init__(
		self,
		edit_view
	):
		self.edit_view = edit_view
		current_value = edit_view.config[
			edit_view.setting_key
		]
		options = get_setting_options(
			edit_view.setting_key,
			current_value
		)

		super().__init__(
			placeholder="Select a value",
			options=[
				discord.SelectOption(
					label=label,
					value=value,
					description=description,
					default=(value == edit_view.pending_value)
				)
				for label, value, description in options
			],
			row=1
		)

	async def callback(
		self,
		interaction: discord.Interaction
	):
		self.edit_view.pending_value = self.values[0]
		self.edit_view.refresh_components()
		await interaction.response.edit_message(
			embed=self.edit_view.create_embed(),
			view=self.edit_view
		)


# -------------------------------------------------------
#                 CHANNEL SETTINGS EDITOR
# -------------------------------------------------------

class ChannelSettingsEditView(
	discord.ui.View
):
	def __init__(
		self,
		config_view
	):
		super().__init__(
			timeout=180
		)
		self.config_view = config_view
		self.page = config_view.page
		self.config = config_view.config.copy()
		self.setting_key = SETTING_GROUPS[
			self.page
		][1][0]
		self.pending_value = str(
			self.config[self.setting_key]
		)
		self.refresh_components()

	def create_embed(self):
		group_name, _ = SETTING_GROUPS[
			self.page
		]
		return discord.Embed(
			title=f"Edit Channel Settings • {group_name}",
			description=(
				f"{SETTING_DESCRIPTIONS[self.setting_key]}\n"
				f"Current value: `{self.config[self.setting_key]}`\n"
				f"New value: `{self.pending_value}`"
			)
		)

	def refresh_components(self):
		self.clear_items()
		self.add_item(
			ChannelSettingSelect(
				self
			)
		)
		self.add_item(
			ChannelValueSelect(
				self
			)
		)
		self.add_item(self.save)
		self.add_item(self.cancel)
		self.add_item(self.back_settings)

	@discord.ui.button(
		label="Save",
		style=discord.ButtonStyle.success,
		row=2
	)
	async def save(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		current_value = self.config[
			self.setting_key
		]
		value = self.pending_value

		if isinstance(current_value, bool):
			value = value == "true"
		elif isinstance(current_value, int):
			value = int(value)

		updated_config = self.config.copy()
		updated_config[self.setting_key] = value
		error = validate_channel_config(
			updated_config
		)

		if error:
			await interaction.response.send_message(
				error,
				ephemeral=True
			)
			return

		update_channel_config(
			self.config_view.guild_id,
			self.config_view.channel_id,
			self.setting_key,
			value
		)
		self.config_view.refresh()
		self.config_view.build_components()

		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.config_view.guild_id,
				self.config_view.channel_id,
				self.config_view.page
			),
			view=self.config_view
		)

	@discord.ui.button(
		label="Cancel",
		style=discord.ButtonStyle.secondary,
		row=2
	)
	async def cancel(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		self.config_view.refresh()
		self.config_view.build_components()
		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.config_view.guild_id,
				self.config_view.channel_id,
				self.config_view.page
			),
			view=self.config_view
		)

	@discord.ui.button(
		label="↩ Back to Settings",
		style=discord.ButtonStyle.secondary,
		row=3
	)
	async def back_settings(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		from ..config_menu import ConfigMenuView

		await interaction.response.edit_message(
			embed=discord.Embed(
				title="Settings",
				description="Choose a settings category."
			),
			view=ConfigMenuView(
				owner=interaction.user,
				guild_id=interaction.guild_id
			)
		)


# -------------------------------------------------------
#                 SETTINGS CATEGORY SELECT
# -------------------------------------------------------

class ChannelCategorySelect(
	discord.ui.Select
):
	def __init__(
		self,
		config_view
	):
		self.config_view = config_view

		options = [
			discord.SelectOption(
				label=group_name,
				value=str(page),
				default=(page == config_view.page)
			)
			for page, (group_name, group_keys)
			in enumerate(SETTING_GROUPS)
		]

		super().__init__(
			placeholder="Select a settings category",
			min_values=1,
			max_values=1,
			options=options,
			row=2
		)

	async def callback(
		self,
		interaction: discord.Interaction
	):
		self.config_view.page = int(
			self.values[0]
		)
		self.config_view.build_components()

		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.config_view.guild_id,
				self.config_view.channel_id,
				self.config_view.page
			),
			view=self.config_view
		)


# -------------------------------------------------------
#                  CHANNEL SETTINGS VIEW
# -------------------------------------------------------

class ChannelConfigView(
	discord.ui.View
):
	def __init__(
		self,
		guild_id,
		channel_id
	):
		super().__init__(
			timeout=180
		)
		self.guild_id = guild_id
		self.channel_id = channel_id
		self.page = 0
		self.refresh()
		self.build_components()

	def refresh(self):
		self.config = get_channel_config(
			self.guild_id,
			self.channel_id
		)

	def build_components(self):
		self.clear_items()

		self.previous_page.disabled = self.page <= 0
		self.next_page.disabled = (
			self.page >= len(SETTING_GROUPS) - 1
		)

		self.add_item(self.previous_page)
		self.add_item(self.next_page)
		self.add_item(
			ChannelCategorySelect(
				self
			)
		)
		self.add_item(self.edit_section)
		self.add_item(self.back_settings)

	async def interaction_check(
		self,
		interaction: discord.Interaction
	):
		if not can_edit_channel_config(
			interaction.user
		):
			await interaction.response.send_message(
				"Administrator or Manage Guild permission required.",
				ephemeral=True
			)
			return False

		return True

	@discord.ui.button(label="Policies", style=discord.ButtonStyle.secondary, row=0)
	async def policies(self, interaction, button):
		await interaction.response.send_modal(
			ChannelSettingsModal(
				self,
				"Sprint Policies",
				[
					("create_sprints", SETTING_DESCRIPTIONS["create_sprints"]),
					("cancel_sprints", SETTING_DESCRIPTIONS["cancel_sprints"]),
					("change_sprint_time", SETTING_DESCRIPTIONS["change_sprint_time"])
				]
			)
		)

	@discord.ui.button(label="Behavior", style=discord.ButtonStyle.secondary, row=0)
	async def behavior(self, interaction, button):
		await interaction.response.send_modal(
			ChannelSettingsModal(
				self,
				"Sprint Behavior",
				[
					(key, SETTING_DESCRIPTIONS[key])
					for key in (
						"allow_join_after_start",
						"allow_leave_after_start",
						"allow_change_duration_after_start",
						"allow_change_waiting_time"
					)
				]
			)
		)

	@discord.ui.button(label="Timing", style=discord.ButtonStyle.secondary, row=0)
	async def timing(self, interaction, button):
		await interaction.response.send_modal(
			ChannelSettingsModal(
				self,
				"Sprint Timing",
				[
					(key, SETTING_DESCRIPTIONS[key])
					for key in (
						"default_duration",
						"min_duration",
						"max_duration",
						"start_waiting_time",
						"word_count_waiting_time"
					)
				]
			)
		)

	@discord.ui.button(label="Empty Sprints", style=discord.ButtonStyle.secondary, row=0)
	async def empty_sprints(self, interaction, button):
		await interaction.response.send_modal(
			ChannelSettingsModal(
				self,
				"Empty Sprint Rules",
				[
					("cancel_empty_sprints", SETTING_DESCRIPTIONS["cancel_empty_sprints"]),
					("empty_sprint_timeout", SETTING_DESCRIPTIONS["empty_sprint_timeout"])
				]
			)
		)

	@discord.ui.button(
		label="◀",
		style=discord.ButtonStyle.secondary,
		row=1
	)
	async def previous_page(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		self.page -= 1
		self.build_components()
		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.guild_id,
				self.channel_id,
				self.page
			),
			view=self
		)

	@discord.ui.button(
		label="▶",
		style=discord.ButtonStyle.secondary,
		row=1
	)
	async def next_page(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		self.page += 1
		self.build_components()
		await interaction.response.edit_message(
			embed=create_channel_config_embed(
				self.guild_id,
				self.channel_id,
				self.page
			),
			view=self
		)

	@discord.ui.button(
		label="Edit Section",
		style=discord.ButtonStyle.primary,
		row=3
	)
	async def edit_section(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		edit_view = ChannelSettingsEditView(
			self
		)

		await interaction.response.edit_message(
			embed=edit_view.create_embed(),
			view=edit_view
		)

	@discord.ui.button(
		label="↩ Back to Settings",
		style=discord.ButtonStyle.secondary,
		row=4
	)
	async def back_settings(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	):
		from ..config_menu import ConfigMenuView

		await interaction.response.edit_message(
			embed=discord.Embed(
				title="Settings",
				description="Choose a settings category."
			),
			view=ConfigMenuView(
				owner=interaction.user,
				guild_id=interaction.guild_id
			)
		)