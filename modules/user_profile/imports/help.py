from modules.help.help_messages import (
    IMPORTS_DESCRIPTION,
    IMPORTS_TITLE
)


def register_help(registry):
    registry.register(
        key="imports",
        label="Imports",
        description="Import data from other bots",
        order=60,
        renderer=lambda: (IMPORTS_TITLE, IMPORTS_DESCRIPTION)
    )