import discord

from .project_list import (
    PROJECT_STATUSES,
    create_project_embed,
    create_project_picker_embed,
    create_projects_embed,
    filter_projects,
    get_project,
    get_user_projects,
    paginate_projects,
    sort_projects,
    update_project
)

from .project_list import delete_project
from modules.user_profile.profile_storage import clear_last_project_if_matches

from .project_modals import (
    CreateProjectModal,
    EditProjectModal
)


# -------------------------------------------------------
#                  PROFILE NAVIGATION
# -------------------------------------------------------

async def send_private_profile(
    interaction,
    owner
):
    from modules.user_profile.profile import (
        ProfileView,
        create_profile_embed
    )

    await interaction.response.defer()

    try:
        await interaction.message.delete()

    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException
    ):
        pass

    await interaction.followup.send(
        embed=create_profile_embed(
            owner
        ),
        view=ProfileView(
            owner=owner
        ),
        ephemeral=True
    )


# -------------------------------------------------------
#                   PROJECT SELECT
# -------------------------------------------------------

class ProjectSelect(
    discord.ui.Select
):
    def __init__(
        self,
        projects,
        selected_project_id=None
    ):
        options = []

        for project in projects:
            project_id = (
                project[
                    "project_id"
                ]
            )

            status = project.get(
                "status",
                "Active"
            )

            wordcount = project.get(
                "wordcount",
                0
            )

            options.append(
                discord.SelectOption(
                    label=project.get(
                        "name",
                        "Untitled"
                    )[:100],
                    value=project_id,
                    description=(
                        f"{status} ✦ "
                        f"{wordcount:,} words"
                    )[:100],
                    default=(
                        project_id
                        == selected_project_id
                    )
                )
            )

        if not options:
            options = [
                discord.SelectOption(
                    label="No projects on this page",
                    value="__none__"
                )
            ]

        super().__init__(
            placeholder="Choose a project",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(
                not projects
            ),
            row=2
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.select_project(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                    STATUS SELECT
# -------------------------------------------------------

class ProjectStatusSelect(
    discord.ui.Select
):
    def __init__(
        self,
        selected_status="Active"
    ):
        options = []

        for status in PROJECT_STATUSES:
            options.append(
                discord.SelectOption(
                    label=status,
                    value=status,
                    default=(
                        status
                        == selected_status
                    )
                )
            )

        super().__init__(
            placeholder="Project status",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.status_selected(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                     SORT SELECT
# -------------------------------------------------------

class ProjectSortSelect(
    discord.ui.Select
):
    def __init__(
        self,
        current_sort
    ):
        options = [
            discord.SelectOption(
                label="Alphabetical",
                value="alphabetical",
                default=(
                    current_sort
                    == "alphabetical"
                )
            ),
            discord.SelectOption(
                label="Status",
                value="status",
                default=(
                    current_sort
                    == "status"
                )
            ),
            discord.SelectOption(
                label="Newest",
                value="newest",
                default=(
                    current_sort
                    == "newest"
                )
            ),
            discord.SelectOption(
                label="Oldest",
                value="oldest",
                default=(
                    current_sort
                    == "oldest"
                )
            )
        ]

        super().__init__(
            placeholder="Sort projects",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.change_sort(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                    FILTER SELECT
# -------------------------------------------------------

class ProjectFilterSelect(
    discord.ui.Select
):
    def __init__(
        self,
        current_filter
    ):
        options = [
            discord.SelectOption(
                label="All statuses",
                value="all",
                default=(
                    current_filter
                    == "all"
                )
            )
        ]

        for status in PROJECT_STATUSES:
            options.append(
                discord.SelectOption(
                    label=status,
                    value=status,
                    default=(
                        current_filter
                        == status
                    )
                )
            )

        super().__init__(
            placeholder="Filter projects",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await self.view.change_filter(
            interaction,
            self.values[0]
        )


# -------------------------------------------------------
#                  CREATE PROJECT VIEW
# -------------------------------------------------------

class CreateProjectView(
    discord.ui.View
):
    def __init__(
        self,
        owner_id: int,
        on_created,
        back_callback=None
    ):
        super().__init__(
            timeout=120
        )

        self.owner_id = owner_id
        self.on_created = on_created
        self.back_callback = back_callback

        self.status = "Active"

        self.add_item(
            ProjectStatusSelect(
                selected_status="Active"
            )
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner_id
        ):
            await interaction.response.send_message(
                "This menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def status_selected(
        self,
        interaction,
        status
    ):
        self.status = status

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Create Project",
                description=(
                    f"Status: **{status}**\n\n"
                    "Continue to enter the project details."
                )
            ),
            view=self
        )

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def continue_creation(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = CreateProjectModal(
            owner_id=self.owner_id,
            status=self.status,
            on_created=self.on_created
        )

        await interaction.response.send_modal(
            modal
        )

    @discord.ui.button(
        label="↩ Back",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.back_callback is None:
            return

        await self.back_callback(
            interaction
        )


# -------------------------------------------------------
#                   PROJECT PICKER
# -------------------------------------------------------

class ProjectPickerView(
    discord.ui.View
):
    def __init__(
        self,
        owner_id: int,
        on_confirm,
        show_last_project=True
    ):
        super().__init__(
            timeout=120
        )

        self.owner_id = owner_id
        self.on_confirm = on_confirm
        self.show_last_project = show_last_project

        self.selected_project_id = None

        self.refresh_components()

    def refresh_components(
        self
    ):
        self.clear_items()

        projects = get_user_projects(
            self.owner_id
        )

        self.add_item(
            ProjectSelect(
                projects[:25],
                selected_project_id=(
                    self.selected_project_id
                )
            )
        )

        self.add_item(
            self.select_button
        )

        self.add_item(
            self.create_button
        )

        if self.show_last_project:
            self.add_item(
                self.last_project_button
            )

        self.select_button.disabled = (
            self.selected_project_id
            is None
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner_id
        ):
            await interaction.response.send_message(
                "This project menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def select_project(
        self,
        interaction,
        project_id
    ):
        project = get_project(
            self.owner_id,
            project_id
        )

        if project is None:
            await interaction.response.send_message(
                "Project not found.",
                ephemeral=True
            )

            return

        self.selected_project_id = (
            project_id
        )

        self.refresh_components()

        await interaction.response.edit_message(
            content=None,
            embed=create_project_picker_embed(
                selected_project=project
            ),
            view=self
        )

    @discord.ui.button(
        label="📚 Select Project",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def select_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        project = get_project(
            self.owner_id,
            self.selected_project_id
        )

        if project is None:
            await interaction.response.send_message(
                "Choose a project first.",
                ephemeral=True
            )

            return

        await self.on_confirm(
            interaction,
            project
        )

    @discord.ui.button(
        label="Create Project",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def create_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        async def back_to_picker(
            back_interaction
        ):
            view = ProjectPickerView(
                owner_id=self.owner_id,
                on_confirm=self.on_confirm,
                show_last_project=(
                    self.show_last_project
                )
            )

            await back_interaction.response.edit_message(
                content=None,
                embed=create_project_picker_embed(),
                view=view
            )

        async def created(
            modal_interaction,
            project
        ):
            await self.on_confirm(
                modal_interaction,
                project
            )

        view = CreateProjectView(
            owner_id=self.owner_id,
            on_created=created,
            back_callback=back_to_picker
        )

        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="Create Project",
                description=(
                    "Choose a status and continue."
                )
            ),
            view=view
        )

    @discord.ui.button(
        label="↩️ Use Last Project",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def last_project_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        from modules.user_profile.profile import (
            get_last_project
        )

        project = get_last_project(
            self.owner_id
        )

        if project is None:
            await interaction.response.send_message(
                "You don't have a previous sprint project yet.",
                ephemeral=True
            )

            return

        await self.on_confirm(
            interaction,
            project
        )


# -------------------------------------------------------
#                 PROJECT DETAIL VIEW
# -------------------------------------------------------

class ProjectDetailView(
    discord.ui.View
):
    def __init__(
        self,
        owner,
        project_id: str
    ):
        super().__init__(
            timeout=180
        )

        self.owner = owner
        self.project_id = project_id

        project = get_project(
            owner.id,
            project_id
        )

        status = (
            project.get(
                "status",
                "Active"
            )
            if project
            else "Active"
        )

        self.add_item(
            ProjectStatusSelect(
                selected_status=status
            )
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner.id
        ):
            await interaction.response.send_message(
                "This project belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def status_selected(
        self,
        interaction,
        status
    ):
        project = update_project(
            user_id=self.owner.id,
            project_id=self.project_id,
            status=status
        )

        await interaction.response.edit_message(
            embed=create_project_embed(
                project
            ),
            view=ProjectDetailView(
                owner=self.owner,
                project_id=self.project_id
            )
        )

    @discord.ui.button(
        label="Edit Details",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def edit_details(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        project = get_project(
            self.owner.id,
            self.project_id
        )

        if project is None:
            await interaction.response.send_message(
                "Project not found.",
                ephemeral=True
            )

            return

        async def updated(
            modal_interaction,
            updated_project
        ):
            await modal_interaction.response.edit_message(
                embed=create_project_embed(
                    updated_project
                ),
                view=ProjectDetailView(
                    owner=self.owner,
                    project_id=self.project_id
                )
            )

        modal = EditProjectModal(
            owner=self.owner,
            project=project,
            on_updated=updated
        )

        await interaction.response.send_modal(
            modal
        )

    @discord.ui.button(
        label="↩ Back to Projects",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def back_projects(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            embed=create_projects_embed(
                self.owner
            ),
            view=UserProjectsView(
                owner=self.owner
            )
        )

    @discord.ui.button(
        label="Delete Project",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def delete_project_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        project = get_project(self.owner.id, self.project_id)
        if project is None:
            await interaction.response.send_message(
                "Project not found.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"Delete \"{project.get('name', 'Untitled')}\"?",
                description=(
                    "This permanently deletes this project.\n"
                    "This action cannot be undone."
                )
            ),
            view=DeleteProjectConfirmationView(
                self.owner,
                self.project_id
            )
        )

# -------------------------------------------------------
#                  BACK TO PROFILE
# -------------------------------------------------------

    @discord.ui.button(
        label="↩Back to Profile",
        style=discord.ButtonStyle.secondary,
        row=4
    )
    async def back_profile(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await send_private_profile(
            interaction,
            self.owner
        )


# -------------------------------------------------------
#                   PROJECTS VIEW
# -------------------------------------------------------

class UserProjectsView(
    discord.ui.View
):
    def __init__(
        self,
        owner,
        sort_mode="alphabetical",
        status_filter="all",
        page=0
    ):
        super().__init__(
            timeout=180
        )

        self.owner = owner

        self.sort_mode = sort_mode
        self.status_filter = status_filter
        self.page = page

        self.page_projects = []
        self.total_pages = 1

        self.build_components()

    def get_filtered_projects(
        self
    ):
        projects = get_user_projects(
            self.owner.id
        )

        projects = filter_projects(
            projects,
            self.status_filter
        )

        projects = sort_projects(
            projects,
            self.sort_mode
        )

        return projects

    def build_components(
        self
    ):
        self.clear_items()

        projects = self.get_filtered_projects()

        (
            self.page_projects,
            self.page,
            self.total_pages
        ) = paginate_projects(
            projects,
            self.page
        )

        self.add_item(
            ProjectSortSelect(
                self.sort_mode
            )
        )

        self.add_item(
            ProjectFilterSelect(
                self.status_filter
            )
        )

        self.add_item(
            ProjectSelect(
                self.page_projects
            )
        )

        self.previous_page.disabled = (
            self.page <= 0
        )

        self.next_page.disabled = (
            self.page
            >= self.total_pages - 1
        )

        self.add_item(
            self.previous_page
        )

        self.add_item(
            self.next_page
        )

        self.add_item(
            self.create_project_button
        )

        self.add_item(
            self.back_profile
        )

    def create_current_embed(
        self
    ):
        return create_projects_embed(
            user=self.owner,
            projects=self.page_projects,
            sort_mode=self.sort_mode,
            status_filter=self.status_filter,
            page=self.page,
            total_pages=self.total_pages
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner.id
        ):
            await interaction.response.send_message(
                "This project menu belongs to another user.",
                ephemeral=True
            )

            return False

        return True

    async def refresh_message(
        self,
        interaction
    ):
        self.build_components()

        await interaction.response.edit_message(
            embed=self.create_current_embed(),
            view=self
        )

    async def change_sort(
        self,
        interaction,
        sort_mode
    ):
        self.sort_mode = sort_mode
        self.page = 0

        await self.refresh_message(
            interaction
        )

    async def change_filter(
        self,
        interaction,
        status_filter
    ):
        self.status_filter = status_filter
        self.page = 0

        await self.refresh_message(
            interaction
        )

    async def select_project(
        self,
        interaction,
        project_id
    ):
        project = get_project(
            self.owner.id,
            project_id
        )

        if project is None:
            await interaction.response.send_message(
                "Project not found.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=create_project_embed(
                project
            ),
            view=ProjectDetailView(
                owner=self.owner,
                project_id=project_id
            )
        )

    @discord.ui.button(
        label="◀",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def previous_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page -= 1

        await self.refresh_message(
            interaction
        )

    @discord.ui.button(
        label="▶",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def next_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page += 1

        await self.refresh_message(
            interaction
        )

    @discord.ui.button(
        label="✚ Create Project",
        style=discord.ButtonStyle.primary,
        row=4
    )
    async def create_project_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        async def created(
            modal_interaction,
            project
        ):
            await modal_interaction.response.edit_message(
                embed=create_project_embed(
                    project
                ),
                view=ProjectDetailView(
                    owner=self.owner,
                    project_id=project[
                        "project_id"
                    ]
                )
            )

        async def back(
            back_interaction
        ):
            view = UserProjectsView(
                owner=self.owner,
                sort_mode=self.sort_mode,
                status_filter=self.status_filter,
                page=self.page
            )

            await back_interaction.response.edit_message(
                embed=view.create_current_embed(),
                view=view
            )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Create Project",
                description=(
                    "Choose a status and continue."
                )
            ),
            view=CreateProjectView(
                owner_id=self.owner.id,
                on_created=created,
                back_callback=back
            )
        )

    @discord.ui.button(
        label="↩Back to Profile",
        style=discord.ButtonStyle.secondary,
        row=4
    )
    async def back_profile(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await send_private_profile(
            interaction,
            self.owner
        )