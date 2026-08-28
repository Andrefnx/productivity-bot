import discord

from modules.common.entitlements import (
    FEATURE_BOT_CUSTOMIZATION,
    is_feature_enabled
)


MAX_NICKNAME_LENGTH = 32
MAX_AVATAR_BYTES = 10 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp"
}


def validate_nickname(value):
    nickname = value.strip()

    if not nickname:
        return None, "Bot name cannot be empty."

    if len(nickname) > MAX_NICKNAME_LENGTH:
        return None, "Bot name must be 32 characters or fewer."

    return nickname, None


def can_manage_bot_appearance(interaction):
    permissions = getattr(
        interaction.user,
        "guild_permissions",
        None
    )
    return permissions is not None and permissions.manage_guild


def is_bot_customization_enabled(interaction):
    return (
        interaction.guild is not None
        and is_feature_enabled(
            FEATURE_BOT_CUSTOMIZATION,
            interaction.guild.id
        )
    )


async def get_bot_member(interaction):
    if interaction.guild is None:
        return None

    bot_member = interaction.guild.me

    if bot_member is not None:
        return bot_member

    return await interaction.guild.fetch_member(
        interaction.client.user.id
    )


async def require_bot_customization(interaction):
    if not is_bot_customization_enabled(interaction):
        await interaction.response.send_message(
            "This feature is not available in this server.",
            ephemeral=True
        )
        return False

    if not can_manage_bot_appearance(interaction):
        await interaction.response.send_message(
            "Manage Guild permission required.",
            ephemeral=True
        )
        return False

    return True


class ChangeBotNameModal(discord.ui.Modal):
    def __init__(self, owner_id):
        super().__init__(title="Change Bot Name")
        self.owner_id = owner_id
        self.nickname_input = discord.ui.TextInput(
            required=True,
            max_length=MAX_NICKNAME_LENGTH
        )
        self.add_item(
            discord.ui.Label(
                text="New bot name for this server",
                component=self.nickname_input
            )
        )

    async def on_submit(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "These settings belong to another user.",
                ephemeral=True
            )
            return

        if not await require_bot_customization(interaction):
            return

        nickname, error = validate_nickname(self.nickname_input.value)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        bot_member = await get_bot_member(interaction)
        if (
            bot_member is None
            or not bot_member.guild_permissions.change_nickname
        ):
            await interaction.response.send_message(
                "I don't have permission to change my nickname in this server.",
                ephemeral=True
            )
            return

        try:
            await bot_member.edit(nick=nickname)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                "I don't have permission to change my nickname in this server.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Bot name updated for this server.",
            ephemeral=True
        )


class ChangeBotAvatarModal(discord.ui.Modal):
    def __init__(self, owner_id):
        super().__init__(title="Change Bot Avatar")
        self.owner_id = owner_id
        self.avatar_upload = discord.ui.FileUpload(
            required=True,
            min_values=1,
            max_values=1
        )
        self.add_item(
            discord.ui.Label(
                text="Server bot avatar",
                description="Upload a PNG, JPEG, or WEBP image.",
                component=self.avatar_upload
            )
        )

    async def on_submit(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "These settings belong to another user.",
                ephemeral=True
            )
            return

        if not await require_bot_customization(interaction):
            return

        if not self.avatar_upload.values:
            await interaction.response.send_message(
                "Upload a PNG, JPEG, or WEBP image.",
                ephemeral=True
            )
            return

        attachment = self.avatar_upload.values[0]
        content_type = (attachment.content_type or "").lower()
        if content_type not in ALLOWED_AVATAR_TYPES:
            await interaction.response.send_message(
                "Upload a PNG, JPEG, or WEBP image.",
                ephemeral=True
            )
            return

        if attachment.size <= 0:
            await interaction.response.send_message(
                "The avatar image cannot be empty.",
                ephemeral=True
            )
            return

        if attachment.size > MAX_AVATAR_BYTES:
            await interaction.response.send_message(
                "The avatar image is too large. Maximum size is 10 MiB.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            avatar = await attachment.read()
            if not avatar:
                raise ValueError("The avatar image cannot be empty.")
            bot_member = await get_bot_member(interaction)
            if bot_member is None:
                raise ValueError("The bot member is unavailable in this server.")
            await bot_member.edit(avatar=avatar)
        except ValueError as error:
            await interaction.followup.send(str(error), ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(
                "Discord could not update the bot avatar in this server.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            "Bot avatar updated for this server.",
            ephemeral=True
        )


class ResetAppearanceConfirmationView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=120)
        self.owner_id = owner_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "These settings belong to another user.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Reset Appearance",
        style=discord.ButtonStyle.danger
    )
    async def confirm(self, interaction, button):
        if not await require_bot_customization(interaction):
            return

        bot_member = await get_bot_member(interaction)
        if (
            bot_member is None
            or not bot_member.guild_permissions.change_nickname
        ):
            await interaction.response.send_message(
                "I don't have permission to reset my appearance in this server.",
                ephemeral=True
            )
            return

        try:
            await bot_member.edit(nick=None, avatar=None)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                "Discord could not reset the bot appearance in this server.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Bot Appearance",
                description="Bot appearance reset for this server."
            ),
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            embed=create_bot_appearance_embed(),
            view=BotAppearanceView(interaction.user)
        )


class BotAppearanceView(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=180)
        self.owner = owner

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "These settings belong to another user.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Change Bot Name",
        style=discord.ButtonStyle.secondary
    )
    async def change_name(self, interaction, button):
        if not await require_bot_customization(interaction):
            return

        await interaction.response.send_modal(ChangeBotNameModal(self.owner.id))

    @discord.ui.button(
        label="Change Bot Avatar",
        style=discord.ButtonStyle.secondary
    )
    async def change_avatar(self, interaction, button):
        if not await require_bot_customization(interaction):
            return

        await interaction.response.send_modal(ChangeBotAvatarModal(self.owner.id))

    @discord.ui.button(
        label="Reset Appearance",
        style=discord.ButtonStyle.danger
    )
    async def reset_appearance(self, interaction, button):
        if not await require_bot_customization(interaction):
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Reset Bot Appearance",
                description=(
                    "This will reset the bot name and avatar for this server."
                )
            ),
            view=ResetAppearanceConfirmationView(self.owner.id),
            ephemeral=True
        )


def create_bot_appearance_embed():
    return discord.Embed(
        title="Bot Appearance",
        description="Customize the bot name and avatar for this server."
    )


async def render_settings(interaction, owner):
    if not is_bot_customization_enabled(interaction):
        await interaction.response.send_message(
            "This feature is not available in this server.",
            ephemeral=True
        )
        return

    await interaction.response.edit_message(
        embed=create_bot_appearance_embed(),
        view=BotAppearanceView(owner)
    )


def register_settings(registry):
    registry.register(
        key="bot_appearance",
        label="Bot Appearance",
        description="Customize the bot name and appearance",
        order=30,
        renderer=render_settings,
        requires_feature=FEATURE_BOT_CUSTOMIZATION
    )
