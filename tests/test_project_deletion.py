import unittest
from unittest.mock import patch

from modules.user_profile.projects.project_list import delete_project


class ProjectDeletionTests(unittest.TestCase):
    def test_delete_project_removes_only_selected_project(self):
        projects = {
            "111111111111111111": {
                "first": {"project_id": "first", "name": "First"},
                "second": {"project_id": "second", "name": "Second"}
            }
        }
        with patch(
            "modules.user_profile.projects.project_list.load_projects",
            return_value=projects
        ), patch(
            "modules.user_profile.projects.project_list.save_projects"
        ) as save:
            self.assertTrue(delete_project(111111111111111111, "first"))
            self.assertFalse(delete_project(111111111111111111, "first"))

        self.assertNotIn("first", projects["111111111111111111"])
        self.assertIn("second", projects["111111111111111111"])
        save.assert_called_once_with(projects)

    def test_delete_missing_project_is_safe(self):
        with patch(
            "modules.user_profile.projects.project_list.load_projects",
            return_value={}
        ):
            self.assertFalse(delete_project(111111111111111111, "missing"))