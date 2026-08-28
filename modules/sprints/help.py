from modules.help.help_messages import (
    SPRINTS_DESCRIPTION,
    SPRINTS_TITLE
)


def register_help(registry):
    registry.register(
        key="sprints",
        label="Sprints",
        description="Joining, progress and results",
        order=10,
        renderer=lambda: (SPRINTS_TITLE, SPRINTS_DESCRIPTION)
    )