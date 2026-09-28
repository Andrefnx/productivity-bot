import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from modules.sprints.sprint_activity import (
    ActivityProjectView,
    start_results_registration
)
from modules.sprints.sprint_results import (
    get_pending_results,
    get_untracked_participants
)
from modules.sprints.system_messages import create_results_embed
from modules.sprints.users import (
    SprintActivityPickerView,
    SprintParticipants,
    SprintUser,
    StartWordCountView
)


async def noop_confirm(interaction, project, initial_wc):
    return None


async def noop_back(interaction):
    return None


class SprintActivitySelectionTests(unittest.TestCase):
    def test_activity_change_reuses_sprint_activity_picker(self):
        self.assertTrue(
            issubclass(ActivityProjectView, SprintActivityPickerView)
        )

    def test_no_project_starting_wc_has_custom_no_wc_and_back(self):
        view = StartWordCountView(
            owner_id=1,
            project=None,
            on_confirm=noop_confirm,
            back_callback=noop_back
        )
        labels = [item.label for item in view.children]

        self.assertEqual(
            labels,
            ["Custom", "No Word Count", "↩ Back"]
        )

    def test_project_starting_wc_has_total_custom_no_wc_and_back(self):
        view = StartWordCountView(
            owner_id=1,
            project={
                "project_id": "p1",
                "name": "Novel",
                "wordcount": 1234
            },
            on_confirm=noop_confirm,
            back_callback=noop_back
        )
        labels = [item.label for item in view.children]

        self.assertEqual(
            labels,
            ["Custom", "Total", "No Word Count", "↩ Back"]
        )

    def test_switch_to_no_project_accepts_custom_starting_wc(self):
        user = SimpleNamespace(id=123)
        sprint_user = SprintUser(
            user=user,
            sprint_id="sprint",
            project=None,
            initial_wc=0
        )

        sprint_user.switch_project(None, initial_wc=250)

        self.assertIsNone(sprint_user.project_id)
        self.assertEqual(sprint_user.project, "No project")
        self.assertEqual(sprint_user.initial_wc, 250)
        self.assertTrue(sprint_user.word_count_enabled)

    def test_switch_to_project_keeps_selected_custom_starting_wc(self):
        user = SimpleNamespace(id=123)
        sprint_user = SprintUser(
            user=user,
            sprint_id="sprint",
            project=None,
            initial_wc=0
        )
        project = {
            "project_id": "p1",
            "name": "Novel",
            "wordcount": 5000
        }

        sprint_user.switch_project(project, initial_wc=25)

        self.assertEqual(sprint_user.project_id, "p1")
        self.assertEqual(sprint_user.project, "Novel")
        self.assertEqual(sprint_user.initial_wc, 25)
        self.assertTrue(sprint_user.word_count_enabled)

    def test_project_can_be_selected_without_word_count(self):
        user = SimpleNamespace(id=123)
        project = {
            "project_id": "p1",
            "name": "Novel",
            "wordcount": 5000
        }
        sprint_user = SprintUser(
            user=user,
            sprint_id="sprint",
            project=project,
            initial_wc=None
        )

        self.assertEqual(sprint_user.project_id, "p1")
        self.assertEqual(sprint_user.project, "Novel")
        self.assertFalse(sprint_user.word_count_enabled)
        self.assertEqual(sprint_user.initial_wc, 0)
        self.assertIn("No word count", sprint_user.get_participant_text())

    def test_no_word_count_user_is_not_pending_result(self):
        participants = SprintParticipants("sprint")
        user = SimpleNamespace(id=123)
        participants.add_user(
            user=user,
            project={"project_id": "p1", "name": "Novel"},
            initial_wc=None
        )

        self.assertEqual(get_pending_results(participants), [])

    def test_no_word_count_user_is_included_in_untracked_results(self):
        participants = SprintParticipants("sprint")
        user = SimpleNamespace(id=123)
        participants.add_user(
            user=user,
            project={"project_id": "p1", "name": "Novel"},
            initial_wc=None
        )

        self.assertEqual(
            get_untracked_participants(participants),
            [participants.get_user(user.id)]
        )

    def test_no_word_count_user_is_shown_without_a_rank(self):
        ranked_user = SimpleNamespace(
            user=SimpleNamespace(display_name="Writer"),
            project="Novel",
            final_wc=1200,
            words_written=200
        )
        untracked_user = SimpleNamespace(
            user=SimpleNamespace(display_name="Planner"),
            project="Outline",
            final_wc=None,
            words_written=None
        )

        embed = create_results_embed(
            [ranked_user],
            [untracked_user]
        )

        self.assertIn("🥇 **Writer**", embed.description)
        self.assertIn("Participants without word count", embed.description)
        self.assertIn("**Planner**", embed.description)
        self.assertNotIn("#2 **Planner**", embed.description)

    def test_finished_message_keeps_mentions_inside_embed_only(self):
        participants = SprintParticipants("sprint")
        participants.add_user(
            user=SimpleNamespace(id=123),
            project=None,
            initial_wc=0
        )
        channel = SimpleNamespace()
        channel.send = AsyncMock(
            return_value=SimpleNamespace(
                edit=AsyncMock(),
                channel=channel
            )
        )

        def close_task(coroutine):
            coroutine.close()
            return Mock()

        with patch(
            "modules.sprints.sprint_activity.asyncio.create_task",
            side_effect=close_task
        ):
            asyncio.run(
                start_results_registration(channel, 60, participants)
            )

        message_kwargs = channel.send.await_args.kwargs
        self.assertNotIn("content", message_kwargs)
        self.assertNotIn("allowed_mentions", message_kwargs)
        self.assertIn(
            "<@123>",
            str(message_kwargs["embed"].to_dict())
        )


if __name__ == "__main__":
    unittest.main()
