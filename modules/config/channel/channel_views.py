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
	"default_waiting_time": "Waiting time used before a sprint starts.",
	"max_waiting_time": "Longest permitted waiting time.",
	"cancel_empty_sprints": "Cancel a sprint when nobody joins.",
	"empty_sprint_timeout": "Seconds to wait before cancelling an empty sprint."
}


def create_channel_config_embed(
	guild_id,
	channel_id
):
	config = get_channel_config(
		guild_id,
		channel_id
	)

	embed = discord.Embed(
		title="Channel Settings",
		description="Settings for this channel."
	)

	for key, value in config.items():
		embed.add_field(
			name=key.replace(
				"_",
				" "
			).title(),
			value=(
				f"{value}\n{SETTING_DESCRIPTIONS[key]}"
			),
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
				label=key.replace(
					"_",
					" "
				).title(),
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
				self.config_view.channel_id
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
		self.refresh()

	def refresh(self):
		self.config = get_channel_config(
			self.guild_id,
			self.channel_id
		)

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

	@discord.ui.button(label="Policies", style=discord.ButtonStyle.secondary)
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

	@discord.ui.button(label="Behavior", style=discord.ButtonStyle.secondary)
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

	@discord.ui.button(label="Timing", style=discord.ButtonStyle.secondary)
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
						"default_waiting_time",
						"max_waiting_time"
					)
				]
			)
		)

	@discord.ui.button(label="Empty Sprints", style=discord.ButtonStyle.secondary)
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