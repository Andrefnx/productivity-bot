IMPORTS_TITLE = "Importing Your Projects"

IMPORTS_DESCRIPTION = (
    "Already used another writing bot? You don't have to "
    "create all your projects again.\n\n"
    "**Importing from Writer Bot**\n\n"
    "1. Open Writer Bot and export your data with `/export`.\n"
    "2. Writer Bot will give you a `.json` file.\n"
    "3. Open `/profile` here.\n"
    "4. Press **Import JSON**.\n"
    "5. Choose **Writer Bot** as the source.\n"
    "6. Upload the file Writer Bot gave you.\n\n"
    "Your projects and their saved information will be "
    "added to your profile automatically."
)


def register_help(registry):
    registry.register(
        key="imports",
        label="Imports",
        description="Import data from other bots",
        order=60,
        renderer=lambda: (IMPORTS_TITLE, IMPORTS_DESCRIPTION)
    )
