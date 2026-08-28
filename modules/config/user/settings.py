from ..config_views import ConfigView, create_config_embed


async def render_settings(interaction, owner):
    await interaction.response.edit_message(
        embed=create_config_embed(owner),
        view=ConfigView(owner=owner)
    )


def register_settings(registry):
    registry.register(
        key="user_settings",
        label="User Settings",
        description="Privacy, timezone and preferences",
        order=10,
        renderer=render_settings
    )