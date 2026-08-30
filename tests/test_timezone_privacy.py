import os
import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.common.runtime_data import ensure_runtime_data_files
from modules.config.config_views import (
    DateTimeSettingsView,
    create_config_embed
)
from modules.config.timezone import (
    get_cached_timezones,
    get_region_timezones,
    get_timezone_display,
    search_timezones
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

    def test_existing_punta_arenas_timezone_is_preserved(self):
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

        self.assertEqual(config["timezone"], LEGACY_DEFAULT_TIMEZONE)
        self.assertEqual(
            profiles["111111111111111111"]["config"]["timezone"],
            LEGACY_DEFAULT_TIMEZONE
        )
        save_profiles.assert_not_called()

    def test_saved_timezone_opens_its_region_and_page(self):
        user = SimpleNamespace(id=111111111111111111)
        timezones = [
            f"America/City_{index:02d}"
            for index in range(30)
        ] + ["America/Punta_Arenas", "Europe/Madrid"]
        with patch(
            "modules.config.config_views.get_user_config",
            return_value={"timezone": "America/Punta_Arenas", "time_format": "12h"}
        ):
            view = DateTimeSettingsView(
                SimpleNamespace(owner=user),
                timezones=timezones
            )

        self.assertEqual(view.selected_region, "America")
        self.assertEqual(view.page, 1)
        timezone_select = next(
            item for item in view.children
            if item.placeholder == "Select timezone"
        )
        selected = next(option for option in timezone_select.options if option.default)
        self.assertEqual(selected.value, "America/Punta_Arenas")
        self.assertEqual(selected.label, "America/Punta Arenas")
        self.assertIsNone(selected.description)

    def test_nested_timezone_is_directly_selectable_in_region(self):
        user = SimpleNamespace(id=111111111111111111)
        with patch(
            "modules.config.config_views.get_user_config",
            return_value={"timezone": "America/Argentina/Buenos_Aires", "time_format": "12h"}
        ):
            view = DateTimeSettingsView(
                SimpleNamespace(owner=user),
                timezones=["America/Argentina/Buenos_Aires"]
            )

        timezone_select = next(
            item for item in view.children
            if item.placeholder == "Select timezone"
        )
        option = timezone_select.options[0]
        self.assertEqual(option.label, "America/Buenos Aires")
        self.assertIsNone(option.description)
        self.assertEqual(option.value, "America/Argentina/Buenos_Aires")

    def test_zoneinfo_database_contains_expected_timezones_when_available(self):
        timezones = get_cached_timezones()
        self.assertGreater(len(timezones), 100)
        for timezone in (
            "America/Santiago",
            "America/Punta_Arenas",
            "America/Argentina/Buenos_Aires"
        ):
            if timezone in timezones:
                self.assertIn(timezone, timezones)

    def test_tzdata_is_declared_for_hosted_timezone_data(self):
        requirements = Path("requirements.txt").read_text().lower()
        self.assertIn("tzdata", requirements)

    def test_america_regions_include_every_source_timezone(self):
        timezones = get_cached_timezones()
        self.assertEqual(
            get_region_timezones("America", timezones),
            sorted(
                (timezone for timezone in timezones if timezone.startswith("America/")),
                key=lambda timezone: (
                    get_timezone_display(timezone)[0].lower(),
                    timezone.lower()
                )
            )
        )

    def test_timezone_display_flattens_to_region_and_location(self):
        self.assertEqual(
            get_timezone_display("America/Argentina/Buenos_Aires")[0],
            "America/Buenos Aires"
        )
        self.assertEqual(
            get_timezone_display("America/Indiana/Indianapolis")[0],
            "America/Indianapolis"
        )

    def test_timezone_pagination_exposes_every_timezone_once(self):
        user = SimpleNamespace(id=111111111111111111)
        timezones = [f"America/City_{index:02d}" for index in range(60)]
        with patch(
            "modules.config.config_views.get_user_config",
            return_value=DEFAULT_CONFIG.copy()
        ):
            view = DateTimeSettingsView(SimpleNamespace(owner=user), timezones=timezones)

        visible_values = []
        for page in range(3):
            view.page = page
            view.build_components()
            timezone_select = next(
                item for item in view.children
                if item.placeholder == "Select timezone"
            )
            self.assertLessEqual(len(timezone_select.options), 25)
            visible_values.extend(option.value for option in timezone_select.options)

        self.assertEqual(visible_values, get_region_timezones("America", timezones))
        self.assertEqual(len(visible_values), len(set(visible_values)))

    def test_search_accepts_flattened_and_canonical_timezone_names(self):
        timezones = [
            "America/Argentina/Buenos_Aires",
            "America/Punta_Arenas",
            "America/Santiago"
        ]
        with patch(
            "modules.config.timezone.get_available_timezones",
            new=AsyncMock(return_value=timezones)
        ):
            for search in (
                "Buenos Aires",
                "America/Buenos Aires",
                "America/Argentina/Buenos_Aires",
                "Punta Arenas",
                "Santiago"
            ):
                self.assertTrue(asyncio.run(search_timezones(search)))

    def test_flattened_name_collisions_keep_all_canonical_values(self):
        user = SimpleNamespace(id=111111111111111111)
        timezones = ["America/Argentina/City", "America/Indiana/City"]
        with patch(
            "modules.config.config_views.get_user_config",
            return_value=DEFAULT_CONFIG.copy()
        ):
            view = DateTimeSettingsView(SimpleNamespace(owner=user), timezones=timezones)

        timezone_select = next(
            item for item in view.children
            if item.placeholder == "Select timezone"
        )
        self.assertEqual({option.value for option in timezone_select.options}, set(timezones))
        self.assertEqual(
            {option.description for option in timezone_select.options},
            {"Argentina", "Indiana"}
        )

    def test_browsing_and_back_do_not_persist_timezone(self):
        user = SimpleNamespace(id=111111111111111111)
        config_view = SimpleNamespace(owner=user, build_components=lambda: None)
        interaction = SimpleNamespace(response=SimpleNamespace(edit_message=AsyncMock()))
        with patch(
            "modules.config.config_views.get_user_config",
            return_value={
                **DEFAULT_CONFIG,
                "timezone": "America/Santiago"
            }
        ), patch("modules.config.config_views.update_user_config") as update:
            view = DateTimeSettingsView(
                config_view,
                timezones=["America/Santiago", "Europe/Madrid"]
            )
            view.selected_region = "Europe"
            asyncio.run(view.back_settings.callback(interaction))

        update.assert_not_called()

    def test_save_persists_only_the_selected_draft_timezone(self):
        user = SimpleNamespace(id=111111111111111111)
        config_view = SimpleNamespace(owner=user, build_components=lambda: None)
        interaction = SimpleNamespace(response=SimpleNamespace(edit_message=AsyncMock()))
        with patch(
            "modules.config.config_views.get_user_config",
            return_value={
                **DEFAULT_CONFIG,
                "timezone": "America/Santiago"
            }
        ), patch("modules.config.config_views.update_user_config") as update:
            view = DateTimeSettingsView(
                config_view,
                timezones=["America/Santiago", "Europe/Madrid"]
            )
            view.draft_timezone = "Europe/Madrid"
            view.selected_timezone = "Europe/Madrid"
            asyncio.run(view.save.callback(interaction))

        update.assert_any_call(user.id, "timezone", "Europe/Madrid")

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