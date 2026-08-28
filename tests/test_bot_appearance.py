import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

import discord

from modules.bot_appearance.help import BOT_PROFILE_CUSTOMIZATION_DESCRIPTION
from modules.bot_appearance.settings import (
    ALLOWED_AVATAR_TYPES,
    BotAppearanceView,
    ChangeBotAvatarModal,
    ChangeBotNameModal,
    ResetAppearanceConfirmationView,
    can_manage_bot_appearance,
    is_bot_customization_enabled,
    validate_nickname
)


class BotAppearanceTests(unittest.TestCase):
    def make_interaction(self, guild_id=111, user_id=42, manage_guild=True):
        messages = []
        permissions = type("Permissions", (), {"manage_guild": manage_guild})()

        class Response:
            async def send_message(self, *args, **kwargs):
                messages.append((args, kwargs))

            async def defer(self, **kwargs):
                messages.append(("defer", kwargs))

            async def edit_message(self, **kwargs):
                messages.append(("edit", kwargs))

            async def send_modal(self, modal):
                messages.append(("modal", modal))

        interaction = type(
            "Interaction",
            (), {
                "guild": type("Guild", (), {"id": guild_id})(),
                "user": type(
                    "User",
                    (), {"id": user_id, "guild_permissions": permissions}
                )(),
                "response": Response(),
                "followup": type("Followup", (), {"send": AsyncMock()})()
            }
        )()
        return interaction, messages

    def test_nickname_validation(self):
        self.assertEqual(validate_nickname("  Focus Bot  "), ("Focus Bot", None))
        self.assertEqual(validate_nickname(" ")[0], None)
        self.assertEqual(validate_nickname("a" * 33)[0], None)

    def test_premium_guild_and_manage_guild_allow_nickname(self):
        interaction, _ = self.make_interaction()
        with patch.dict(os.environ, {"PREMIUM_GUILD_IDS": "111"}, clear=True):
            self.assertTrue(is_bot_customization_enabled(interaction))
            self.assertTrue(can_manage_bot_appearance(interaction))

    def test_non_premium_guild_blocks_direct_interaction(self):
        interaction, messages = self.make_interaction(guild_id=222)
        view = BotAppearanceView(interaction.user)
        with patch.dict(os.environ, {"PREMIUM_GUILD_IDS": "111"}, clear=True):
            asyncio.run(view.change_name.callback(interaction))
        self.assertEqual(
            messages[0][0][0],
            "This feature is not available in this server."
        )

    def test_buttons_have_per_server_labels_and_styles(self):
        interaction, _ = self.make_interaction()
        view = BotAppearanceView(interaction.user)
        buttons = {item.label: item.style for item in view.children}
        self.assertEqual(buttons["Change Bot Name"], discord.ButtonStyle.secondary)
        self.assertEqual(buttons["Change Bot Avatar"], discord.ButtonStyle.secondary)
        self.assertEqual(buttons["Reset Appearance"], discord.ButtonStyle.danger)
        self.assertNotIn("Global Bot Avatar", buttons)
        self.assertNotIn("Reset Bot Name", buttons)

    def test_avatar_upload_accepts_png_and_jpeg(self):
        self.assertIn("image/png", ALLOWED_AVATAR_TYPES)
        self.assertIn("image/jpeg", ALLOWED_AVATAR_TYPES)
        self.assertNotIn("image/gif", ALLOWED_AVATAR_TYPES)

    def test_avatar_upload_rejects_invalid_mime_and_empty_file(self):
        for content_type, size, expected_message in (
            ("image/gif", 4, "Upload a PNG, JPEG, or WEBP image."),
            ("image/png", 0, "The avatar image cannot be empty.")
        ):
            interaction, messages = self.make_interaction()
            attachment = type(
                "Attachment",
                (), {
                    "content_type": content_type,
                    "size": size,
                    "read": AsyncMock(return_value=b"")
                }
            )()
            modal = ChangeBotAvatarModal(42)
            modal.avatar_upload._values = [attachment]

            with patch.dict(
                os.environ,
                {"PREMIUM_GUILD_IDS": "111"},
                clear=True
            ):
                asyncio.run(modal.on_submit(interaction))

            self.assertEqual(messages[0][0][0], expected_message)

    def test_name_edit_targets_current_guild_member_only(self):
        interaction, _ = self.make_interaction()
        bot_member = type(
            "Member",
            (), {
                "guild_permissions": type("Permissions", (), {"change_nickname": True})(),
                "edit": AsyncMock()
            }
        )()
        interaction.guild.me = bot_member
        modal = ChangeBotNameModal(42)
        modal.nickname_input._value = "Focus Bot"
        with patch.dict(os.environ, {"PREMIUM_GUILD_IDS": "111"}, clear=True):
            asyncio.run(modal.on_submit(interaction))
        bot_member.edit.assert_awaited_once_with(nick="Focus Bot")

    def test_avatar_edit_targets_current_guild_member_only(self):
        interaction, _ = self.make_interaction()
        bot_member = type("Member", (), {"edit": AsyncMock()})()
        interaction.guild.me = bot_member
        attachment = type(
            "Attachment",
            (), {
                "content_type": "image/png",
                "size": 4,
                "read": AsyncMock(return_value=b"PNG!")
            }
        )()
        modal = ChangeBotAvatarModal(42)
        modal.avatar_upload._values = [attachment]
        with patch.dict(os.environ, {"PREMIUM_GUILD_IDS": "111"}, clear=True):
            asyncio.run(modal.on_submit(interaction))
        bot_member.edit.assert_awaited_once_with(avatar=b"PNG!")
        self.assertFalse(hasattr(interaction, "client"))

    def test_reset_resets_nickname_and_avatar_on_current_guild_member(self):
        interaction, _ = self.make_interaction()
        bot_member = type(
            "Member",
            (), {
                "guild_permissions": type("Permissions", (), {"change_nickname": True})(),
                "edit": AsyncMock()
            }
        )()
        interaction.guild.me = bot_member
        view = ResetAppearanceConfirmationView(42)
        with patch.dict(os.environ, {"PREMIUM_GUILD_IDS": "111"}, clear=True):
            asyncio.run(view.confirm.callback(interaction))
        bot_member.edit.assert_awaited_once_with(nick=None, avatar=None)

    def test_help_does_not_describe_global_appearance(self):
        lower_description = BOT_PROFILE_CUSTOMIZATION_DESCRIPTION.lower()
        self.assertNotIn("global", lower_description)
        self.assertNotIn("every server", lower_description)
        self.assertNotIn("owner-only", lower_description)


if __name__ == "__main__":
    unittest.main()
