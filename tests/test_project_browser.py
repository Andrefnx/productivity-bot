import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.user_profile.projects.project_list import (
    filter_projects,
    sort_projects
)
from modules.user_profile.projects.project_views import (
    DeleteProjectConfirmationView,
    ProjectPickerView
)


class ProjectBrowserTests(unittest.TestCase):
    def projects(self):
        return [
            {
                "project_id": str(index),
                "name": f"Project {index:02d}",
                "status": "Active" if index % 2 else "Draft",
                "wordcount": index,
                "created_at": "01-01-2026"
            }
            for index in range(30)
        ]

    def test_picker_pages_through_every_project_with_safe_embeds(self):
        projects = self.projects()
        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=projects
        ):
            view = ProjectPickerView(1, AsyncMock())
            seen_ids = []
            for page in range(view.total_pages):
                view.page = page
                view.refresh_components()
                embed = view.create_current_embed()
                seen_ids.extend(
                    project["project_id"]
                    for project in view.page_projects
                )
                self.assertLessEqual(len(embed.fields), 25)

        self.assertEqual(seen_ids, [str(index) for index in range(30)])

    def test_sorting_and_status_filtering_are_deterministic(self):
        projects = self.projects()
        alphabetical = sort_projects(projects, "alphabetical")
        drafts = filter_projects(alphabetical, "Draft")

        self.assertEqual(
            [project["name"] for project in alphabetical],
            sorted(project["name"] for project in projects)
        )
        self.assertTrue(all(project["status"] == "Draft" for project in drafts))

    def test_delete_confirmation_deletes_only_once(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        interaction = SimpleNamespace(
            user=owner,
            response=SimpleNamespace(
                edit_message=AsyncMock(),
                send_message=AsyncMock()
            )
        )
        confirmation = DeleteProjectConfirmationView(owner, "project")

        with patch(
            "modules.user_profile.projects.project_views.delete_project",
            return_value=True
        ) as delete, patch(
            "modules.user_profile.projects.project_views.clear_last_project_if_matches"
        ) as clear_last, patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=[]
        ):
            asyncio.run(confirmation.confirm_delete.callback(interaction))

        delete.assert_called_once_with(1, "project")
        clear_last.assert_called_once_with(1, "project")
        interaction.response.edit_message.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()