PROJECTS_TITLE = "Projects"

PROJECTS_DESCRIPTION = (
    "**Opening your projects**\n\n"
    "Use `/profile` and press **My Projects**.\n\n"
    "Your project list shows up to 5 projects per page.\n\n"
    "You can sort projects by:\n"
    "• Alphabetical order\n"
    "• Status\n"
    "• Newest\n"
    "• Oldest\n\n"
    "You can also filter the list to show only projects with "
    "a specific status.\n\n"
    "**Creating a project**\n\n"
    "Press **Create Project**, choose a status, then enter:\n"
    "• Project name\n"
    "• Description\n"
    "• Current word count\n"
    "• Word count goal\n\n"
    "**Project information**\n\n"
    "A project can store:\n"
    "• Name\n"
    "• Description\n"
    "• Status\n"
    "• Word count\n"
    "• Goal\n"
    "• Creation date\n\n"
    "If a goal is set, the bot also shows how much of the goal "
    "you have completed.\n\n"
    "**Editing a project**\n\n"
    "Open the project to **Edit Details** or **Delete Project**. "
    "Deleting a project asks for confirmation.\n\n"
    "You can also change the project's status directly from "
    "the project page."
)


def register_help(registry):
    registry.register(
        key="projects",
        label="Projects",
        description="Create, edit and organize projects",
        order=20,
        renderer=lambda: (PROJECTS_TITLE, PROJECTS_DESCRIPTION)
    )
