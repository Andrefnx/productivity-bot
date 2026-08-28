from .help_messages import (
    GETTING_STARTED_DESCRIPTION,
    GETTING_STARTED_TITLE
)


def register_help(registry):
    registry.register(
        key="getting_started",
        label="Getting Started",
        description="Commands and basic navigation",
        order=0,
        renderer=lambda: (
            GETTING_STARTED_TITLE,
            GETTING_STARTED_DESCRIPTION
        )
    )