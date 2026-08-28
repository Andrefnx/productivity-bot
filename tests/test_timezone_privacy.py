import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from modules.common.runtime_data import ensure_runtime_data_files
from modules.config.config_views import (
    DateTimeSettingsView,
    create_config_embed
)
from modules.config.user.user_config import (
    DEFAULT_CONFIG,
    LEGACY_DEFAULT_TIMEZONE,
    get_user_config
)


class TimezonePrivacyTests(unittest.TestCase):
    def test_new_user_timezone_default_is_none(self):
        with patch(
            "modules.user_profile.profile_storage.load_profiles",
            return_value={}
        ):
            self.assertIsNone(get_user_config(111111111111111111)["timezone"])

    def test_new_user_ui_shows_not_set(self):
        user = type("User", (), {"id": 111111111111111111})()
        with patch(
            "modules.config.config_views.get_user_config",
            return_value=DEFAULT_CONFIG.copy()
        ):
            embed = create_config_embed(user)
            view = DateTimeSettingsView(
                type("ConfigView", (), {"owner": user})(),
                timezones=["UTC"]
            )

        self.assertIn("Not set", embed.fields[1].value)
        self.assertIn("Timezone: `Not set`", view.create_embed().description)
        self.assertFalse(view.timezone_is_set)

    def test_saved_timezone_is_preserved(self):
        saved_timezone = "UTC"
        with patch(
            "modules.user_profile.profile_storage.load_profiles",
            return_value={
                "111111111111111111": {
                    "config": {"timezone": saved_timezone}
                }
            }
        ):
            config = get_user_config(111111111111111111)

        self.assertEqual(config["timezone"], saved_timezone)

    def test_technical_selection_does_not_change_unset_preference(self):
        user = type("User", (), {"id": 111111111111111111})()
        with patch(
            "modules.config.config_views.get_user_config",
            return_value=DEFAULT_CONFIG.copy()
        ):
            view = DateTimeSettingsView(
                type("ConfigView", (), {"owner": user})(),
                timezones=["UTC"]
            )

        self.assertEqual(view.selected_timezone, "UTC")
        self.assertFalse(view.timezone_is_set)

    def test_timezone_none_is_supported_in_configuration_data(self):
        with patch(
            "modules.user_profile.profile_storage.load_profiles",
            return_value={
                "111111111111111111": {
                    "config": {"timezone": None}
                }
            }
        ):
            config = get_user_config(111111111111111111)

        self.assertIsNone(config["timezone"])

    def test_legacy_default_timezone_is_migrated_to_none(self):
        profiles = {
            "111111111111111111": {
                "config": {"timezone": LEGACY_DEFAULT_TIMEZONE}
            }
        }
        with patch(
            "modules.user_profile.profile_storage.load_profiles",
            return_value=profiles
        ), patch(
            "modules.user_profile.profile_storage.save_profiles"
        ) as save_profiles:
            config = get_user_config(111111111111111111)

        self.assertIsNone(config["timezone"])
        self.assertIsNone(profiles["111111111111111111"]["config"]["timezone"])
        save_profiles.assert_called_once_with(profiles)

    def test_legacy_timezone_migration_is_idempotent(self):
        profiles = {
            "111111111111111111": {
                "config": {"timezone": LEGACY_DEFAULT_TIMEZONE}
            }
        }
        with patch(
            "modules.user_profile.profile_storage.load_profiles",
            return_value=profiles
        ), patch(
            "modules.user_profile.profile_storage.save_profiles"
        ) as save_profiles:
            get_user_config(111111111111111111)
            get_user_config(111111111111111111)

        self.assertEqual(save_profiles.call_count, 1)

    def test_missing_runtime_data_files_are_created(self):
        with TemporaryDirectory() as temporary_directory:
            ensure_runtime_data_files(temporary_directory)
            data_directory = Path(temporary_directory)

            self.assertEqual(
                (data_directory / "profiles.json").read_text(),
                "{}"
            )
            self.assertEqual(
                (data_directory / "projects.json").read_text(),
                "{}"
            )
            self.assertEqual(
                (data_directory / "channel_config.json").read_text(),
                "{}"
            )
            self.assertEqual(
                (data_directory / "sprint_users.json").read_text(),
                "{}"
            )
            self.assertEqual(
                (data_directory / "active_sprints.json").read_text(),
                "[]"
            )

    def test_runtime_initializer_does_not_overwrite_existing_files(self):
        with TemporaryDirectory() as temporary_directory:
            data_directory = Path(temporary_directory)
            profiles_file = data_directory / "profiles.json"
            profiles_file.write_text('{"existing": true}')

            ensure_runtime_data_files(temporary_directory)

            self.assertEqual(
                profiles_file.read_text(),
                '{"existing": true}'
            )

    def test_runtime_data_and_env_are_ignored(self):
        gitignore = Path(".gitignore").read_text()

        self.assertIn(".env", gitignore)
        self.assertIn("data/*.json", gitignore)
        self.assertIn("!data/.gitkeep", gitignore)
        self.assertFalse(Path(".env").is_symlink())


if __name__ == "__main__":
    unittest.main()