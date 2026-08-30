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
    ProjectPickerView,
    UserProjectsView
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

    def test_project_browser_returns_content_and_compact_state_embeds(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=self.projects()
        ):
            view = UserProjectsView(owner)
            content, state = view.create_current_embeds()

        self.assertEqual(len(content.fields), 5)
        self.assertEqual(content.title, "Owner's Projects")
        self.assertIsNone(content.description)
        self.assertEqual(
            state.description,
            "**Alphabetical** ✦ **All statuses** ✦ **Page 1/6**"
        )
        self.assertIsNone(state.title)
        self.assertEqual(len(state.fields), 0)

    def test_sort_filter_and_page_refresh_both_embeds(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        interaction = SimpleNamespace(
            response=SimpleNamespace(edit_message=AsyncMock())
        )
        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=self.projects()
        ):
            view = UserProjectsView(owner)
            asyncio.run(view.change_filter(interaction, "Draft"))
            embeds = interaction.response.edit_message.await_args.kwargs["embeds"]
            self.assertIn("**Draft**", embeds[1].description)

            asyncio.run(view.next_page.callback(interaction))
            embeds = interaction.response.edit_message.await_args.kwargs["embeds"]
            self.assertIn("**Page 2/3**", embeds[1].description)

            asyncio.run(view.change_sort(interaction, "newest"))
            embeds = interaction.response.edit_message.await_args.kwargs["embeds"]
            self.assertIn("**Newest**", embeds[1].description)
            self.assertIn("**Page 1/3**", embeds[1].description)

    def test_navigation_buttons_disable_at_browser_boundaries(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=self.projects()
        ):
            first_page = UserProjectsView(owner)
            last_page = UserProjectsView(owner, page=5)

        self.assertTrue(first_page.previous_page.disabled)
        self.assertFalse(first_page.next_page.disabled)
        self.assertFalse(last_page.previous_page.disabled)
        self.assertTrue(last_page.next_page.disabled)

    def test_empty_filter_has_content_empty_state_and_browser_state(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        with patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=[self.projects()[0]]
        ):
            view = UserProjectsView(owner, status_filter="Completed")
            content, state = view.create_current_embeds()

        self.assertEqual(content.fields[0].name, "No projects match this filter.")
        self.assertIn("**Completed**", state.description)
        project_select = next(
            item for item in view.children
            if getattr(item, "placeholder", None) == "Choose a project"
        )
        self.assertTrue(project_select.disabled)

    def test_back_from_detail_preserves_browser_state(self):
        owner = SimpleNamespace(id=1, display_name="Owner")
        interaction = SimpleNamespace(
            response=SimpleNamespace(edit_message=AsyncMock())
        )
        project = self.projects()[0]
        with patch(
            "modules.user_profile.projects.project_views.get_project",
            return_value=project
        ), patch(
            "modules.user_profile.projects.project_views.get_user_projects",
            return_value=self.projects()
        ):
            view = UserProjectsView(owner, sort_mode="newest", status_filter="Draft", page=1)
            asyncio.run(view.select_project(interaction, project["project_id"]))
            detail = interaction.response.edit_message.await_args.kwargs["view"]
            asyncio.run(detail.back_projects.callback(interaction))

        browser = interaction.response.edit_message.await_args.kwargs["view"]
        self.assertEqual(browser.sort_mode, "newest")
        self.assertEqual(browser.status_filter, "Draft")
        self.assertEqual(browser.page, 1)
        self.assertEqual(len(interaction.response.edit_message.await_args.kwargs["embeds"]), 2)

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