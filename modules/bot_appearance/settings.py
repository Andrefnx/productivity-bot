import os

import discord

from modules.common.entitlements import (
    FEATURE_BOT_CUSTOMIZATION,
    is_feature_enabled
)


MAX_NICKNAME_LENGTH = 32
RESET_NICKNAME = None
MAX_AVATAR_BYTES = 10 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif"
}


def is_bot_owner(user_id):
    owner_id = os.getenv("BOT_OWNER_ID")
    return owner_id is not None and str(user_id) == owner_id


def validate_nickname(value):
    nickname = value.strip()

    if not nickname:
        return None, "Bot name cannot be empty."

    if len(nickname) > MAX_NICKNAME_LENGTH:
        return (
            None,
            "Bot name must be 32 characters or fewer."
        )

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

        if not is_bot_customization_enabled(interaction):
            await interaction.response.send_message(
                "This feature is not available in this server.",
                ephemeral=True
            )
            return

        if not can_manage_bot_appearance(interaction):
            await interaction.response.send_message(
                "Manage Guild permission required.",
                ephemeral=True
            )
            return

        nickname, error = validate_nickname(
            self.nickname_input.value
        )

        if error:
            await interaction.response.send_message(
                error,
                ephemeral=True
            )
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
        super().__init__(title="Global Bot Avatar")
        self.owner_id = owner_id
        self.avatar_upload = discord.ui.FileUpload(
            required=True,
            min_values=1,
            max_values=1
        )
        self.add_item(
            discord.ui.Label(
                text="Global bot avatar",
                description=(
                    "Upload a PNG, JPEG, WEBP, or GIF image."
                ),
                component=self.avatar_upload
            )
        )

    async def on_submit(self, interaction):
        if not is_bot_owner(interaction.user.id):
            await interaction.response.send_message(
                "Only the configured bot owner can change the global avatar.",
                ephemeral=True
            )
            return

        attachment = self.avatar_upload.values[0]
        content_type = (attachment.content_type or "").lower()

        if content_type not in ALLOWED_AVATAR_TYPES:
            await interaction.response.send_message(
                "Upload a PNG, JPEG, WEBP, or GIF image.",
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
            await interaction.client.user.edit(avatar=avatar)
        except discord.HTTPException as error:
            if error.status == 429:
                message = (
                    "Discord rate-limited the avatar change. "
                    "Please wait before trying again."
                )
            else:
                message = "Discord could not update the global bot avatar."
            await interaction.followup.send(
                message,
                ephemeral=True
            )
            return

        await interaction.followup.send(
            "Global bot avatar updated. It may take a moment to appear in every server.",
            ephemeral=True
        )


class AvatarConfirmationView(discord.ui.View):
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
        label="Confirm Global Avatar Change",
        style=discord.ButtonStyle.danger
    )
    async def confirm(self, interaction, button):
        if not is_bot_owner(interaction.user.id):
            await interaction.response.send_message(
                "Only the configured bot owner can change the global avatar.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ChangeBotAvatarModal(self.owner_id)
        )


class BotAppearanceView(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=180)
        self.owner = owner

        if not is_bot_owner(owner.id):
            self.remove_item(self.global_avatar)

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
        style=discord.ButtonStyle.primary
    )
    async def change_name(self, interaction, button):
        if not is_bot_customization_enabled(interaction):
            await interaction.response.send_message(
                "This feature is not available in this server.",
                ephemeral=True
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "Bot appearance is only available in a server.",
                ephemeral=True
            )
            return

        if not can_manage_bot_appearance(interaction):
            await interaction.response.send_message(
                "Manage Guild permission required.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ChangeBotNameModal(self.owner.id)
        )

    @discord.ui.button(
        label="Reset Bot Name",
        style=discord.ButtonStyle.secondary
    )
    async def reset_name(self, interaction, button):
        if not is_bot_customization_enabled(interaction):
            await interaction.response.send_message(
                "This feature is not available in this server.",
                ephemeral=True
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "Bot appearance is only available in a server.",
                ephemeral=True
            )
            return

        if not can_manage_bot_appearance(interaction):
            await interaction.response.send_message(
                "Manage Guild permission required.",
                ephemeral=True
            )
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
            await bot_member.edit(nick=RESET_NICKNAME)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                "I don't have permission to change my nickname in this server.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Bot name reset for this server.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Global Bot Avatar",
        style=discord.ButtonStyle.danger
    )
    async def global_avatar(self, interaction, button):
        if not is_bot_owner(interaction.user.id):
            await interaction.response.send_message(
                "Only the configured bot owner can change the global avatar.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Global Bot Avatar",
                description=(
                    "This will change the bot avatar in every server."
                )
            ),
            view=AvatarConfirmationView(self.owner.id),
            ephemeral=True
        )


def create_bot_appearance_embed():
    return discord.Embed(
        title="Bot Appearance",
        description=(
            "Customize the bot name for this server. "
            "The global avatar changes in every server."
        )
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