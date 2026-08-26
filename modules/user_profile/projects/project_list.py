import json
import os
import uuid

from datetime import datetime

import discord


# -------------------------------------------------------
#                   PROJECT STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

PROJECTS_FILE = os.path.join(
    DATA_DIRECTORY,
    "projects.json"
)

PROJECT_STATUSES = [
    "Active",
    "Draft",
    "Editing",
    "Paused",
    "Completed"
]

PROJECTS_PER_PAGE = 5


def load_projects():
    if not os.path.exists(
        PROJECTS_FILE
    ):
        return {}

    try:
        with open(
            PROJECTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):
        return {}


def save_projects(
    projects
):
    os.makedirs(
        DATA_DIRECTORY,
        exist_ok=True
    )

    with open(
        PROJECTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            projects,
            file,
            indent=4,
            ensure_ascii=False
        )


# -------------------------------------------------------
#                    PROJECT DATA
# -------------------------------------------------------

def get_user_projects(
    user_id: int
):
    projects = load_projects()

    user_projects = projects.get(
        str(user_id),
        {}
    )

    return list(
        user_projects.values()
    )


def get_project(
    user_id: int,
    project_id: str
):
    projects = load_projects()

    user_projects = projects.get(
        str(user_id),
        {}
    )

    return user_projects.get(
        project_id
    )


def create_project(
    user_id: int,
    name: str,
    description: str = "",
    status: str = "Active",
    wordcount: int = 0,
    goal=None
):
    projects = load_projects()

    user_key = str(
        user_id
    )

    user_projects = projects.get(
        user_key,
        {}
    )

    project_id = str(
        uuid.uuid4()
    )

    project = {
        "project_id": project_id,
        "name": name.strip(),
        "description": description.strip(),
        "status": status,
        "wordcount": wordcount,
        "goal": goal,
        "created_at": datetime.now().strftime(
            "%d-%m-%Y"
        )
    }

    user_projects[
        project_id
    ] = project

    projects[
        user_key
    ] = user_projects

    save_projects(
        projects
    )

    return project


def update_project(
    user_id: int,
    project_id: str,
    name=None,
    description=None,
    status=None,
    wordcount=None,
    goal="__unchanged__",
    created_at="__unchanged__"
):
    projects = load_projects()

    user_key = str(
        user_id
    )

    user_projects = projects.get(
        user_key,
        {}
    )

    project = user_projects.get(
        project_id
    )

    if project is None:
        return None

    if name is not None:
        project["name"] = (
            name.strip()
        )

    if description is not None:
        project["description"] = (
            description.strip()
        )

    if status is not None:
        project["status"] = status

    if wordcount is not None:
        project["wordcount"] = wordcount

    if goal != "__unchanged__":
        project["goal"] = goal

    if created_at != "__unchanged__":
        project["created_at"] = (
            created_at
        )

    user_projects[
        project_id
    ] = project

    projects[
        user_key
    ] = user_projects

    save_projects(
        projects
    )

    return project


# -------------------------------------------------------
#                   PROJECT DATES
# -------------------------------------------------------

def parse_created_date(
    value
):
    value = value.strip()

    if not value:
        return None

    try:
        date = datetime.strptime(
            value,
            "%d-%m-%Y"
        )

    except ValueError:
        return False

    return date.strftime(
        "%d-%m-%Y"
    )


def get_created_date(
    project
):
    value = project.get(
        "created_at"
    )

    if not value:
        return None

    try:
        date = datetime.strptime(
            value,
            "%d-%m-%Y"
        )

        return date.strftime(
            "%d-%m-%Y"
        )

    except ValueError:
        pass

    try:
        date = datetime.fromisoformat(
            value
        )

        return date.strftime(
            "%d-%m-%Y"
        )

    except (
        ValueError,
        TypeError
    ):
        return None


def get_created_sort_value(
    project
):
    value = get_created_date(
        project
    )

    if not value:
        return datetime.min

    try:
        return datetime.strptime(
            value,
            "%d-%m-%Y"
        )

    except ValueError:
        return datetime.min


# -------------------------------------------------------
#                  PROJECT PROGRESS
# -------------------------------------------------------

def get_project_progress(
    project
):
    wordcount = project.get(
        "wordcount",
        0
    )

    goal = project.get(
        "goal"
    )

    if (
        goal is None
        or goal <= 0
    ):
        return None

    return (
        wordcount
        / goal
        * 100
    )


def get_progress_bar(
    progress
):
    if progress is None:
        return "No goal set"

    display_progress = min(
        max(
            progress,
            0
        ),
        100
    )

    filled = round(
        display_progress
        / 10
    )

    empty = (
        10
        - filled
    )

    return (
        f"{'■' * filled}"
        f"{'□' * empty} "
        f"**{progress:.1f}%**"
    )


# -------------------------------------------------------
#                  PROJECT SORTING
# -------------------------------------------------------

def sort_projects(
    projects,
    sort_mode
):
    if sort_mode == "alphabetical":
        return sorted(
            projects,
            key=lambda project: (
                project.get(
                    "name",
                    ""
                ).lower()
            )
        )

    if sort_mode == "status":
        status_order = {
            "Active": 0,
            "Draft": 1,
            "Editing": 2,
            "Paused": 3,
            "Completed": 4
        }

        return sorted(
            projects,
            key=lambda project: (
                status_order.get(
                    project.get(
                        "status"
                    ),
                    99
                ),
                project.get(
                    "name",
                    ""
                ).lower()
            )
        )

    if sort_mode == "newest":
        return sorted(
            projects,
            key=get_created_sort_value,
            reverse=True
        )

    if sort_mode == "oldest":
        return sorted(
            projects,
            key=get_created_sort_value
        )

    return projects


# -------------------------------------------------------
#                  PROJECT FILTERING
# -------------------------------------------------------

def filter_projects(
    projects,
    status_filter
):
    if status_filter == "all":
        return projects

    return [
        project
        for project
        in projects
        if project.get(
            "status",
            "Active"
        ) == status_filter
    ]


# -------------------------------------------------------
#                  PROJECT PAGINATION
# -------------------------------------------------------

def paginate_projects(
    projects,
    page
):
    total_pages = max(
        1,
        (
            len(projects)
            + PROJECTS_PER_PAGE
            - 1
        )
        // PROJECTS_PER_PAGE
    )

    page = max(
        0,
        min(
            page,
            total_pages - 1
        )
    )

    start = (
        page
        * PROJECTS_PER_PAGE
    )

    end = (
        start
        + PROJECTS_PER_PAGE
    )

    return (
        projects[
            start:end
        ],
        page,
        total_pages
    )


# -------------------------------------------------------
#                  PROJECT SUMMARY
# -------------------------------------------------------

def get_project_summary(
    project
):
    status = project.get(
        "status",
        "Active"
    )

    wordcount = project.get(
        "wordcount",
        0
    )

    goal = project.get(
        "goal"
    )

    progress = get_project_progress(
        project
    )

    if goal is None:
        return (
            f"{status} ✦ "
            f"{wordcount:,} words"
        )

    return (
        f"{status} ✦ "
        f"{wordcount:,} / "
        f"{goal:,} words ✦ "
        f"{progress:.1f}%"
    )


# -------------------------------------------------------
#                   PROJECT EMBED
# -------------------------------------------------------

def create_project_embed(
    project
):
    name = project.get(
        "name",
        "Untitled"
    )

    description = (
        project.get(
            "description"
        )
        or "No description."
    )

    status = project.get(
        "status",
        "Active"
    )

    wordcount = project.get(
        "wordcount",
        0
    )

    goal = project.get(
        "goal"
    )

    progress = get_project_progress(
        project
    )

    created = get_created_date(
        project
    )

    embed = discord.Embed(
        title=name,
        description=description
    )

    embed.add_field(
        name="Status",
        value=f"**{status}**",
        inline=True
    )

    embed.add_field(
        name="Word Count",
        value=f"**{wordcount:,}**",
        inline=True
    )

    embed.add_field(
        name="Goal",
        value=(
            f"**{goal:,}**"
            if goal is not None
            else "Not set"
        ),
        inline=True
    )

    embed.add_field(
        name="Progress",
        value=get_progress_bar(
            progress
        ),
        inline=False
    )

    embed.add_field(
        name="Created",
        value=(
            created
            if created
            else (
                "Unknown — use "
                "**Edit Details** to set it."
            )
        ),
        inline=False
    )

    return embed


# -------------------------------------------------------
#                  PROJECT PICKER EMBED
# -------------------------------------------------------

def create_project_picker_embed(
    selected_project=None
):
    if selected_project is None:
        return discord.Embed(
            title="Choose a project",
            description=(
                "Select one of your projects, "
                "create a new one, or reuse "
                "your last sprint project."
            )
        )

    return create_project_embed(
        selected_project
    )


# -------------------------------------------------------
#                   PROJECTS EMBED
# -------------------------------------------------------

def create_projects_embed(
    user,
    projects=None,
    sort_mode="alphabetical",
    status_filter="all",
    page=0,
    total_pages=1
):
    if projects is None:
        projects = get_user_projects(
            user.id
        )

    sort_labels = {
        "alphabetical": "Alphabetical",
        "status": "Status",
        "newest": "Newest",
        "oldest": "Oldest"
    }

    filter_label = (
        "All statuses"
        if status_filter == "all"
        else status_filter
    )

    embed = discord.Embed(
        title=f"{user.display_name}'s Projects",
        description=(
            f"**{sort_labels.get(sort_mode, 'Alphabetical')}**"
            f" ✦ **{filter_label}**"
            f" ✦ **Page {page + 1}/{total_pages}**"
        )
    )

    if not projects:
        embed.add_field(
            name="No projects found",
            value=(
                "There are no projects matching "
                "the current filter."
            ),
            inline=False
        )

        return embed

    for project in projects:
        name = project.get(
            "name",
            "Untitled"
        )

        embed.add_field(
            name=name,
            value=get_project_summary(
                project
            ),
            inline=False
        )

    return embed