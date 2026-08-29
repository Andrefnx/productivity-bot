import discord

from .imports import (
    ImportSourceView
)

from .profile_storage import (
    get_profile,
    set_last_project
)

from .projects import (
    UserProjectsView,
    create_projects_embed,
    get_project
)

# -------------------------------------------------------
#                 LAST SPRINT PROJECT
# -------------------------------------------------------

def get_last_project(
    user_id: int
):
    profile = get_profile(
        user_id
    )

    project_id = profile.get(
        "last_project_id"
    )

    if not project_id:
        return None

    return get_project(
        user_id=user_id,
        project_id=project_id
    )


# -------------------------------------------------------
#                   PROFILE EMBED
# -------------------------------------------------------

def create_profile_embed(
    user
):
    from modules.economy import (
        calculate_level,
        get_coins,
        get_xp_progress
    )

    profile = get_profile(
        user.id
    )

    last_project = get_last_project(
        user.id
    )

    last_project_name = (
        last_project.get(
            "name"
        )
        if last_project
        else "None yet"
    )

    embed = discord.Embed(
        title=user.display_name
    )

    embed.add_field(
        name="Level",
        value=(
            f"{calculate_level(profile.get('xp', 0))} ✦ "
            f"{get_xp_progress(profile.get('xp', 0))} / 100 XP"
        ),
        inline=False
    )

    embed.add_field(
        name="Balance",
        value=(
            f"Total XP ✦ {profile.get('xp', 0)}\n"
            f"Coins ✦ {get_coins(user.id)}"
        ),
        inline=False
    )

    embed.add_field(
        name="Last project in sprints",
        value=last_project_name,
        inline=False
    )

    embed.set_thumbnail(
        url=user.display_avatar.url
    )

    return embed


# -------------------------------------------------------
#                    PROFILE VIEW
# -------------------------------------------------------

class ProfileView(
    discord.ui.View
):
    def __init__(
        self,
        owner
    ):
        super().__init__(
            timeout=180
        )

        self.owner = owner

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if (
            interaction.user.id
            != self.owner.id
        ):
            await interaction.response.send_message(
                "This profile belongs to another user.",
                ephemeral=True
            )

            return False

        return True


# -------------------------------------------------------
#                    MY PROJECTS
# -------------------------------------------------------

    @discord.ui.button(
        label="My Projects",
        style=discord.ButtonStyle.primary
    )
    async def my_projects(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        from modules.config import (
            get_user_config
        )

        from modules.user_profile.projects import (
            UserProjectsView
        )

        config = get_user_config(
            self.owner.id
        )

        projects_private = (
            config[
                "projects_visibility"
            ]
            == "private"
        )

        projects_view = UserProjectsView(
            owner=self.owner
        )

        projects_embed = (
            projects_view.create_current_embed()
        )

        if projects_private:
            await interaction.response.send_message(
                embed=projects_embed,
                view=projects_view,
                ephemeral=True
            )

            return

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
            embed=projects_embed,
            view=projects_view,
            ephemeral=False
        )
# -------------------------------------------------------
#                    IMPORT JSON
# -------------------------------------------------------

    @discord.ui.button(
        label="Import JSON",
        style=discord.ButtonStyle.secondary
    )
    async def import_json(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Import JSON",
            description=(
                "Where does your export come from?"
            )
        )

        view = ImportSourceView(
            owner_id=self.owner.id
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )
        
# -------------------------------------------------------
#                      SETTINGS
# -------------------------------------------------------

    @discord.ui.button(
        label="Settings",
        style=discord.ButtonStyle.secondary
    )
    async def settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        from modules.config.user.user_views import (
            ConfigView,
            create_config_embed
        )

        await interaction.response.edit_message(
            embed=create_config_embed(
                self.owner
            ),
            view=ConfigView(
                owner=self.owner
            )
        )