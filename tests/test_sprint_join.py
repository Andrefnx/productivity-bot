import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import SprintView
from modules.sprints.users import JoinSprintView, StartWordCountView


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

    def test_join_project_opens_start_word_count_choice(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project = {
            "project_id": "project-1",
            "name": "Test Project",
            "wordcount": 100
        }
        join_view = JoinSprintView(sprint, interaction.user.id)
        with patch.dict("os.environ", {}, clear=True):
            asyncio.run(join_view.join_project(interaction, project))

        self.assertFalse(sprint.participants.has_user(interaction.user.id))
        self.assertIsInstance(
            interaction.response.edit_message.await_args.kwargs["view"],
            StartWordCountView
        )

    def test_total_start_adds_existing_project_without_timezone_change(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project = {
            "project_id": "project-1",
            "name": "Test Project",
            "wordcount": 100
        }
        start_view = StartWordCountView(sprint, interaction.user.id, project)
        sprint.update_current_message = AsyncMock()

        with patch("modules.sprints.users.set_last_project"):
            asyncio.run(start_view.total.callback(interaction))

        self.assertTrue(sprint.participants.has_user(interaction.user.id))
        self.assertEqual(
            sprint.participants.get_user(interaction.user.id).initial_wc,
            100
        )
        sprint.update_current_message.assert_awaited_once()

    def test_back_from_project_allows_joining_without_project(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project = {
            "project_id": "project-1",
            "name": "Test Project",
            "wordcount": 100
        }
        start_view = StartWordCountView(sprint, interaction.user.id, project)

        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=[]
        ):
            asyncio.run(start_view.back.callback(interaction))

        picker = interaction.response.edit_message.await_args.kwargs["view"]
        self.assertIsInstance(picker, JoinSprintView)

        asyncio.run(picker.no_project.callback(interaction))
        no_project_view = interaction.response.edit_message.await_args.kwargs["view"]
        self.assertIsNone(no_project_view.project)
        self.assertFalse(sprint.participants.has_user(interaction.user.id))

    def test_back_allows_selecting_another_project_once(self):
        sprint = self.create_sprint()
        interaction = self.create_interaction()
        project_a = {"project_id": "a", "name": "A", "wordcount": 1}
        project_b = {"project_id": "b", "name": "B", "wordcount": 200}
        start_view = StartWordCountView(sprint, interaction.user.id, project_a)
        sprint.update_current_message = AsyncMock()

        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=[]
        ), patch("modules.sprints.users.set_last_project"):
            asyncio.run(start_view.back.callback(interaction))
            picker = interaction.response.edit_message.await_args.kwargs["view"]
            asyncio.run(picker.join_project(interaction, project_b))
            second_start_view = interaction.response.edit_message.await_args.kwargs["view"]
            asyncio.run(second_start_view.total.callback(interaction))

        self.assertEqual(len(sprint.participants), 1)
        self.assertEqual(
            sprint.participants.get_user(interaction.user.id).project_id,
            "b"
        )

    def test_no_project_start_view_hides_total_and_keeps_back(self):
        sprint = self.create_sprint()
        start_view = StartWordCountView(sprint, 111111111111111111, None)
        labels = [item.label for item in start_view.children]

        self.assertEqual(labels, ["Custom", "↩ Back"])

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