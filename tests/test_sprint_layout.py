import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import (
    SprintSettingsMenuView,
    SprintTimeView,
    SprintView
)
from modules.sprints.help import SPRINTS_DESCRIPTION
from modules.sprints.settings import SprintSettingsView


class SprintLayoutTests(unittest.TestCase):
    def create_sprint(self):
        return SprintView(
            duration=30,
            starts_in=5,
            creator_id=111111111111111111,
            guild_id=222222222222222222,
            channel_id=333333333333333333,
            channel_config=DEFAULT_CHANNEL_CONFIG.copy(),
            sprint_config=DEFAULT_SPRINT_CONFIG.copy()
        )

    def test_sprint_buttons_have_exact_rows(self):
        sprint = self.create_sprint()
        rows = {}
        for item in sprint.children:
            rows.setdefault(item.row, []).append(item.label)

        self.assertEqual(rows[0], ["Join", "Leave"])
        self.assertEqual(rows[1], ["Change My Sprint Activity"])
        self.assertEqual(rows[2], ["Sprint Settings"])
        self.assertEqual(rows[3], ["Cancel Sprint"])

    def test_settings_menu_contains_time_settings_and_back(self):
        menu = SprintSettingsMenuView(self.create_sprint())
        labels = [item.label for item in menu.children]

        self.assertEqual(
            labels,
            ["Sprint Time", "Edit Settings", "↩ Back"]
        )

    def test_sprint_time_view_has_edit_and_back(self):
        time_view = SprintTimeView(self.create_sprint())
        labels = [item.label for item in time_view.children]

        self.assertEqual(labels, ["Edit Time", "↩ Back"])

    def test_edit_settings_has_save_and_back(self):
        sprint = self.create_sprint()
        settings_view = SprintSettingsView(
            sprint,
            back_view=SprintSettingsMenuView(sprint)
        )
        labels = [item.label for item in settings_view.children if hasattr(item, "label")]

        self.assertIn("Save", labels)
        self.assertIn("↩ Back", labels)

    def test_edit_settings_uses_draft_until_save(self):
        sprint = self.create_sprint()
        settings_view = SprintSettingsView(
            sprint,
            back_view=SprintSettingsMenuView(sprint)
        )

        settings_view.draft_config["empty_sprint_timeout"] = 120

        self.assertIsNone(sprint.sprint_config["empty_sprint_timeout"])

    def test_sprint_time_edit_uses_existing_modal_flow(self):
        sprint = self.create_sprint()
        time_view = SprintTimeView(sprint)
        interaction = SimpleNamespace()
        sprint.open_change_sprint_time = AsyncMock()

        asyncio.run(time_view.edit_time.callback(interaction))

        sprint.open_change_sprint_time.assert_awaited_once_with(interaction)

    def test_help_uses_current_sprint_labels(self):
        self.assertIn("Change My Sprint Activity", SPRINTS_DESCRIPTION)
        self.assertIn("Sprint Settings", SPRINTS_DESCRIPTION)
        self.assertIn("Sprint Time", SPRINTS_DESCRIPTION)
        self.assertIn("Edit Settings", SPRINTS_DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
