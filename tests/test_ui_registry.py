import os
import unittest
from unittest.mock import patch

from modules.common.entitlements import FEATURE_BOT_CUSTOMIZATION
from modules.common.ui.registry import UIRegistry
from modules.config.config_menu import ConfigMenuView
from modules.help.help_messages import (
    PROJECTS_DESCRIPTION,
    SETTINGS_DESCRIPTION,
    SPRINTS_DESCRIPTION
)
from modules.help.help_views import HelpSelect
from modules.ui_registry import (
    get_help_registry,
    get_settings_registry
)


class UIRegistryTests(unittest.TestCase):
    def test_entries_are_ordered(self):
        registry = UIRegistry("test")
        registry.register("second", "Second", "", 20, lambda: None)
        registry.register("first", "First", "", 10, lambda: None)

        self.assertEqual(
            [entry.key for entry in registry.entries()],
            ["first", "second"]
        )

    def test_private_entries_are_hidden(self):
        registry = UIRegistry("test")
        registry.register("public", "Public", "", 10, lambda: None)
        registry.register(
            "private",
            "Private",
            "",
            20,
            lambda: None,
            public=False
        )

        self.assertEqual(
            [entry.key for entry in registry.entries()],
            ["public"]
        )

    def test_duplicate_keys_raise_clear_error(self):
        registry = UIRegistry("help")
        registry.register("entry", "Entry", "", 10, lambda: None)

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate help registry key: entry"
        ):
            registry.register("entry", "Entry", "", 20, lambda: None)

    def test_help_and_settings_are_independent(self):
        help_registry = UIRegistry("help")
        settings_registry = UIRegistry("settings")
        help_registry.register("same", "Help", "", 10, lambda: None)
        settings_registry.register("same", "Settings", "", 10, lambda: None)

        self.assertEqual(help_registry.get("same").label, "Help")
        self.assertEqual(settings_registry.get("same").label, "Settings")

    def test_public_registries_exclude_marketplace(self):
        help_keys = [entry.key for entry in get_help_registry().entries(111)]
        settings_keys = [
            entry.key
            for entry in get_settings_registry().entries(111)
        ]

        self.assertNotIn("marketplace", help_keys)
        self.assertNotIn("marketplace", settings_keys)

    def test_global_menus_use_registry_entries(self):
        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            help_labels = [
                option.label
                for option in HelpSelect(111).options
            ]
            owner = type("Owner", (), {"id": 1})()
            settings_labels = [
                option.label
                for option in ConfigMenuView(owner, 111).children[0].options
            ]

        self.assertIn("Bot Profile Customization", help_labels)
        self.assertNotIn("Marketplace", help_labels)
        self.assertEqual(
            settings_labels,
            ["User Settings", "Channel Settings", "Bot Appearance"]
        )

    def test_settings_help_describes_only_base_settings(self):
        self.assertIn("User Settings", SETTINGS_DESCRIPTION)
        self.assertIn("Channel Settings", SETTINGS_DESCRIPTION)
        self.assertNotIn("Bot Appearance", SETTINGS_DESCRIPTION)
        self.assertNotIn("Marketplace", SETTINGS_DESCRIPTION)

    def test_help_describes_current_sprint_and_project_flows(self):
        self.assertIn("No Project", SPRINTS_DESCRIPTION)
        self.assertIn("Custom", SPRINTS_DESCRIPTION)
        self.assertIn("Total", SPRINTS_DESCRIPTION)
        self.assertIn("Delete Project", PROJECTS_DESCRIPTION)

    def test_premium_entries_are_hidden_for_normal_guild_and_dm(self):
        registry = UIRegistry("test")
        registry.register("base", "Base", "", 10, lambda: None)
        registry.register(
            "premium",
            "Premium",
            "",
            20,
            lambda: None,
            requires_feature=FEATURE_BOT_CUSTOMIZATION
        )

        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            self.assertEqual(
                [entry.key for entry in registry.entries(111)],
                ["base", "premium"]
            )
            self.assertEqual(
                [entry.key for entry in registry.entries(222)],
                ["base"]
            )
            self.assertEqual(
                [entry.key for entry in registry.entries(None)],
                ["base"]
            )

    def test_private_entry_stays_hidden_in_premium_guild(self):
        registry = UIRegistry("test")
        registry.register(
            "private_premium",
            "Private Premium",
            "",
            10,
            lambda: None,
            public=False,
            requires_feature=FEATURE_BOT_CUSTOMIZATION
        )

        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            self.assertEqual(registry.entries(111), [])


if __name__ == "__main__":
    unittest.main()