SPRINTS_TITLE = "Sprints"

SPRINTS_DESCRIPTION = (
    "**Starting a sprint**\n\n"
    "Use `/sprint` and choose how long the sprint should last "
    "and when it should begin.\n\n"
    "Once created, the sprint message will appear in the channel.\n\n"
    "**Joining**\n\n"
    "Press **Join** and choose a project or **No Project**.\n\n"
    "You can:\n"
    "• Select an existing project\n"
    "• Create a new project\n"
    "• Use your last sprint project\n"
    "• Join without a project\n\n"
    "After choosing the activity, choose **Total** to use a project's "
    "current word count, **Custom** to start from 0 or another value, or "
    "**No Word Count** to participate without tracking words.\n\n"
    "**During the sprint**\n\n"
    "You can leave the sprint or use **Change My Sprint Activity** "
    "to change what you're working on.\n\n"
    "Changing activity reuses the same project and starting word count flow "
    "as joining: choose a project or **No Project**, then choose the available "
    "word count mode. Projects offer **Total**, **Custom**, or "
    "**No Word Count**; **No Project** offers **Custom** or "
    "**No Word Count**.\n\n"
    "Use **Sprint Settings** and choose **Sprint Time** to change timing, "
    "or **Edit Settings** to change session overrides.\n\n"
    "If you change projects, you can register the progress you "
    "made on the previous activity before switching.\n\n"
    "**When the sprint ends**\n\n"
    "Participants who tracked a word count can register their final "
    "word count. Participants using **No Word Count** still receive "
    "participation rewards without a word count prompt.\n\n"
    "For tracked word counts, you can enter either:\n"
    "• Your new total word count\n"
    "• Only the number of words you added or removed\n\n"
    "Use only one of those options.\n\n"
    "Once registration is complete, the sprint results are posted."
)


def register_help(registry):
    registry.register(
        key="sprints",
        label="Sprints",
        description="Joining, progress and results",
        order=10,
        renderer=lambda: (SPRINTS_TITLE, SPRINTS_DESCRIPTION)
    )
