import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modules.sprints.sprint_activity import (
    register_difference,
    register_new_total
)
from modules.sprints.users import SprintParticipants


class SprintWordCountTests(unittest.TestCase):
    def make_user(self, project=None, initial_wc=0):
        user = SimpleNamespace(
            id=111111111111111111,
            display_name="Test User",
            mention="<@111111111111111111>"
        )
        participants = SprintParticipants("sprint-1")
        with patch("modules.sprints.users.set_last_project"):
            participants.add_user(user, project, initial_wc)
        return participants.get_user(user.id)

    def test_total_start_adds_only_progress_to_project(self):
        sprint_user = self.make_user(
            {"project_id": "project", "name": "Project", "wordcount": 123062},
            123062
        )
        with patch("modules.sprints.sprint_activity.add_project_words") as add:
            register_new_total(sprint_user, 123562)
        add.assert_called_once_with(
            user_id=111111111111111111,
            project_id="project",
            words=500
        )

    def test_custom_zero_adds_only_progress_to_project(self):
        sprint_user = self.make_user(
            {"project_id": "project", "name": "Project", "wordcount": 123062},
            0
        )
        with patch("modules.sprints.sprint_activity.add_project_words") as add:
            register_new_total(sprint_user, 500)
        add.assert_called_once_with(
            user_id=111111111111111111,
            project_id="project",
            words=500
        )

    def test_custom_start_adds_only_difference_to_project(self):
        sprint_user = self.make_user(
            {"project_id": "project", "name": "Project", "wordcount": 123062},
            100
        )
        with patch("modules.sprints.sprint_activity.add_project_words") as add:
            register_new_total(sprint_user, 350)
        add.assert_called_once_with(
            user_id=111111111111111111,
            project_id="project",
            words=250
        )

    def test_no_project_adds_positive_progress_outside_projects(self):
        sprint_user = self.make_user(None, 0)
        with patch(
            "modules.sprints.sprint_activity.add_words_outside_projects"
        ) as add:
            register_new_total(sprint_user, 500)
        add.assert_called_once_with(111111111111111111, 500)

    def test_no_project_negative_progress_is_not_subtracted(self):
        sprint_user = self.make_user(None, 1000)
        with patch(
            "modules.sprints.sprint_activity.add_words_outside_projects"
        ) as add:
            register_new_total(sprint_user, 800)
        add.assert_not_called()

    def test_difference_word_count_uses_positive_progress_only(self):
        sprint_user = self.make_user(None, 100)
        with patch(
            "modules.sprints.sprint_activity.add_words_outside_projects"
        ) as add:
            register_difference(sprint_user, -20)
        add.assert_not_called()

    def test_no_project_participant_is_displayed_consistently(self):
        sprint_user = self.make_user(None, 123)
        self.assertIn("No project", sprint_user.get_participant_text())
        self.assertIn("123 words", sprint_user.get_participant_text())