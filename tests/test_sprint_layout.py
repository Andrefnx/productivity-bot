import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.help.help_messages import SPRINTS_DESCRIPTION
from modules.sprints.active_sprint import (
    SprintSettingsMenuView,
    SprintView
)


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
        self.assertEqual(rows[1], ["Sprint Activity"])
        self.assertEqual(rows[2], ["Sprint Settings"])
        self.assertEqual(rows[3], ["Cancel Sprint"])
        self.assertNotIn("Change Sprint Time", rows[0] + rows[1] + rows[2] + rows[3])

    def test_settings_menu_contains_time_and_existing_settings(self):
        menu = SprintSettingsMenuView(self.create_sprint())
        labels = [item.label for item in menu.children]

        self.assertEqual(
            labels,
            ["Change Sprint Time", "Edit Sprint Settings", "↩ Back"]
        )

    def test_settings_menu_time_uses_existing_modal_flow(self):
        sprint = self.create_sprint()
        menu = SprintSettingsMenuView(sprint)
        interaction = SimpleNamespace(response=SimpleNamespace(send_modal=AsyncMock()))

        with patch.object(sprint, "open_change_sprint_time", new=AsyncMock()) as open_time:
            asyncio.run(menu.change_time.callback(interaction))

        open_time.assert_awaited_once_with(interaction)

    def test_help_uses_current_sprint_labels(self):
        self.assertIn("Sprint Activity", SPRINTS_DESCRIPTION)
        self.assertIn("Sprint Settings", SPRINTS_DESCRIPTION)
        self.assertIn("change sprint time", SPRINTS_DESCRIPTION.lower())


if __name__ == "__main__":
    unittest.main()