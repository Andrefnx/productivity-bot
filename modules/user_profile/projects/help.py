from modules.help.help_messages import (
    PROJECTS_DESCRIPTION,
    PROJECTS_TITLE
)


def register_help(registry):
    registry.register(
        key="projects",
        label="Projects",
        description="Create, edit and organize projects",
        order=20,
        renderer=lambda: (PROJECTS_TITLE, PROJECTS_DESCRIPTION)
    )