import asyncio
import os
import unittest
from unittest.mock import patch

from modules.bot_appearance.settings import (
    BotAppearanceView,
    RESET_NICKNAME,
    can_manage_bot_appearance,
    is_bot_customization_enabled,
    is_bot_owner,
    validate_nickname
)


class BotAppearanceTests(unittest.TestCase):
    def test_owner_authorization(self):
        with patch.dict(os.environ, {"BOT_OWNER_ID": "42"}):
            self.assertTrue(is_bot_owner(42))
            self.assertFalse(is_bot_owner(24))

    def test_missing_owner_disables_global_avatar(self):
        with patch.dict(os.environ, {}, clear=True):
            owner = type("Owner", (), {"id": 42})()
            labels = [item.label for item in BotAppearanceView(owner).children]

        self.assertFalse(is_bot_owner(42))
        self.assertNotIn("Global Bot Avatar", labels)

    def test_nickname_validation(self):
        self.assertEqual(validate_nickname("  Focus Bot  "), ("Focus Bot", None))
        self.assertEqual(validate_nickname(" ")[0], None)
        self.assertEqual(validate_nickname("a" * 33)[0], None)

    def test_reset_uses_no_nickname(self):
        self.assertIsNone(RESET_NICKNAME)

    def test_global_avatar_is_owner_only(self):
        with patch.dict(
            os.environ,
            {
                "BOT_OWNER_ID": "42",
                "PREMIUM_GUILD_IDS": "111"
            }
        ):
            owner = type("Owner", (), {"id": 42})()
            labels = [item.label for item in BotAppearanceView(owner).children]

        self.assertIn("Global Bot Avatar", labels)

    def test_premium_guild_and_manage_guild_allow_nickname(self):
        permissions = type("Permissions", (), {"manage_guild": True})()
        interaction = type(
            "Interaction",
            (), {
                "guild": type("Guild", (), {"id": 111})(),
                "user": type("User", (), {"guild_permissions": permissions})()
            }
        )()

        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            self.assertTrue(is_bot_customization_enabled(interaction))
            self.assertTrue(can_manage_bot_appearance(interaction))

    def test_non_premium_guild_blocks_direct_interaction(self):
        messages = []

        class Response:
            async def send_message(self, message, ephemeral):
                messages.append((message, ephemeral))

        interaction = type(
            "Interaction",
            (), {
                "guild": type("Guild", (), {"id": 222})(),
                "user": type(
                    "User",
                    (), {
                        "id": 42,
                        "guild_permissions": type(
                            "Permissions",
                            (), {"manage_guild": True}
                        )()
                    }
                )(),
                "response": Response()
            }
        )()
        view = BotAppearanceView(interaction.user)

        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            asyncio.run(view.change_name.callback(interaction))

        self.assertEqual(
            messages,
            [("This feature is not available in this server.", True)]
        )

    def test_premium_admin_is_not_global_avatar_owner(self):
        with patch.dict(
            os.environ,
            {
                "BOT_OWNER_ID": "42",
                "PREMIUM_GUILD_IDS": "111"
            },
            clear=True
        ):
            self.assertFalse(is_bot_owner(24))
            self.assertTrue(is_bot_owner(42))

    def test_owner_can_open_global_avatar_in_normal_guild(self):
        responses = []

        class Response:
            async def send_message(self, **kwargs):
                responses.append(kwargs)

        user = type("User", (), {"id": 42})()
        interaction = type(
            "Interaction",
            (), {
                "guild": type("Guild", (), {"id": 222})(),
                "user": user,
                "response": Response()
            }
        )()
        view = BotAppearanceView(user)

        with patch.dict(
            os.environ,
            {
                "BOT_OWNER_ID": "42",
                "PREMIUM_GUILD_IDS": "111"
            },
            clear=True
        ):
            asyncio.run(view.global_avatar.callback(interaction))

        self.assertEqual(
            responses[0]["embed"].title,
            "Global Bot Avatar"
        )
        self.assertTrue(responses[0]["ephemeral"])

    def test_non_owner_admin_cannot_open_global_avatar(self):
        for guild_id in (111, 222):
            messages = []

            class Response:
                async def send_message(self, message, ephemeral):
                    messages.append((message, ephemeral))

            user = type("User", (), {"id": 24})()
            interaction = type(
                "Interaction",
                (), {
                    "guild": type("Guild", (), {"id": guild_id})(),
                    "user": user,
                    "response": Response()
                }
            )()
            view = BotAppearanceView(user)

            with patch.dict(
                os.environ,
                {
                    "BOT_OWNER_ID": "42",
                    "PREMIUM_GUILD_IDS": "111"
                },
                clear=True
            ):
                asyncio.run(view.global_avatar.callback(interaction))

            self.assertEqual(
                messages,
                [("Only the configured bot owner can change the global avatar.", True)]
            )


if __name__ == "__main__":
    unittest.main()