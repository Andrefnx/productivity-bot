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


if __name__ == "__main__":
    unittest.main()