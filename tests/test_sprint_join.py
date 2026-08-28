import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import SprintView
from modules.sprints.users import JoinSprintView


class SprintJoinTests(unittest.TestCase):
    def create_sprint(self):
        return SprintView(
            creator_id=111111111111111111,
            guild_id=222222222222222222,
            channel_id=333333333333333333,
            duration=30,
            starts_in=5,
            channel_config=DEFAULT_CHANNEL_CONFIG.copy(),
            sprint_config=DEFAULT_SPRINT_CONFIG.copy()
        )

    def create_interaction(self, user_id=111111111111111111):
        response = SimpleNamespace(
            send_message=AsyncMock(),
            edit_message=AsyncMock(),
            is_done=lambda: False
        )
        user = SimpleNamespace(
            id=user_id,
            display_name="Test User",
            mention="<@111111111111111111>"
        )
        return SimpleNamespace(user=user, response=response)

    def test_join_with_timezone_none_responds_with_project_picker(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()

        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=[]
        ):
            asyncio.run(sprint.join.callback(interaction))

        interaction.response.send_message.assert_awaited_once()
        self.assertIsInstance(
            interaction.response.send_message.await_args.kwargs["view"],
            JoinSprintView
        )

    def test_join_constructor_error_sends_controlled_response(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()

        with patch(
            "modules.sprints.active_sprint.JoinSprintView",
            side_effect=RuntimeError("test failure")
        ), patch("builtins.print") as print_mock:
            asyncio.run(sprint.join.callback(interaction))

        interaction.response.send_message.assert_awaited_once_with(
            "Unable to open the sprint join menu. Please try again.",
            ephemeral=True
        )
        print_mock.assert_any_call("ERROR OPENING SPRINT JOIN:")

    def test_join_project_adds_existing_project_without_timezone_change(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project = {
            "project_id": "project-1",
            "name": "Test Project",
            "wordcount": 100
        }
        join_view = JoinSprintView(sprint, interaction.user.id)
        sprint.update_current_message = AsyncMock()

        with patch(
            "modules.sprints.users.set_last_project"
        ), patch.dict("os.environ", {}, clear=True):
            asyncio.run(join_view.join_project(interaction, project))

        self.assertTrue(sprint.participants.has_user(interaction.user.id))
        self.assertEqual(
            sprint.participants.get_user(interaction.user.id).initial_wc,
            100
        )
        interaction.response.edit_message.assert_awaited_once()
        sprint.update_current_message.assert_awaited_once()

    def test_leave_still_responds_and_removes_participant(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project = {
            "project_id": "project-1",
            "name": "Test Project",
            "wordcount": 100
        }
        sprint.update_current_message = AsyncMock()

        with patch("modules.sprints.users.set_last_project"):
            sprint.participants.add_user(interaction.user, project)

        asyncio.run(sprint.leave.callback(interaction))

        self.assertFalse(sprint.participants.has_user(interaction.user.id))
        interaction.response.send_message.assert_awaited_once_with(
            "You left the sprint!",
            ephemeral=True
        )
        sprint.update_current_message.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()