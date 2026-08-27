from datetime import datetime

from modules.user_profile.profile_storage import (
    load_profiles,
    save_profiles
)

from modules.economy import calculate_level

from modules.user_profile.projects.project_list import (
    load_projects,
    save_projects
)


# -------------------------------------------------------
#                    STATUS MAPPING
# -------------------------------------------------------

WRITER_BOT_STATUS_MAP = {
    "InProgress": "Active",
    "Planning": "Draft",
    "Editing": "Editing",
    "Published": "Completed"
}


# -------------------------------------------------------
#                     DATE HELPERS
# -------------------------------------------------------

def convert_timestamp(
    timestamp
):
    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(
            int(timestamp)
        ).strftime(
            "%d-%m-%Y"
        )

    except (
        ValueError,
        TypeError,
        OSError
    ):
        return None


# -------------------------------------------------------
#                    PROJECT MAPPING
# -------------------------------------------------------

def convert_writer_bot_project(
    project
):
    writer_bot_id = project.get(
        "id"
    )

    source_project_id = (
        f"writer_bot:{writer_bot_id}"
    )

    original_status = project.get(
        "status"
    )

    if project.get(
        "completed"
    ):
        status = "Completed"

    else:
        status = WRITER_BOT_STATUS_MAP.get(
            original_status,
            "Draft"
        )

    return {
        "project_id": source_project_id,
        "name": project.get(
            "title"
        )
        or "Untitled",
        "description": project.get(
            "description"
        )
        or "",
        "status": status,
        "wordcount": project.get(
            "wordcount",
            0
        )
        or 0,
        "goal": project.get(
            "project_goal"
        ),
        "created_at": convert_timestamp(
            project.get(
                "created_at"
            )
        ),
        "source": {
            "type": "writer_bot",
            "project_id": writer_bot_id
        },
        "source_data": project
    }


# -------------------------------------------------------
#                  PROJECT IMPORT
# -------------------------------------------------------

def import_writer_bot_projects(
    user_id: int,
    source_projects
):
    projects_data = load_projects()

    user_key = str(
        user_id
    )

    user_projects = projects_data.get(
        user_key,
        {}
    )

    created = 0
    updated = 0

    for source_project in source_projects:
        converted = convert_writer_bot_project(
            source_project
        )

        project_id = converted[
            "project_id"
        ]

        if project_id in user_projects:
            existing = user_projects[
                project_id
            ]

            existing.update(
                converted
            )

            user_projects[
                project_id
            ] = existing

            updated += 1

        else:
            user_projects[
                project_id
            ] = converted

            created += 1

    projects_data[
        user_key
    ] = user_projects

    save_projects(
        projects_data
    )

    return {
        "created": created,
        "updated": updated,
        "total": len(
            source_projects
        )
    }


# -------------------------------------------------------
#                   PROFILE IMPORT
# -------------------------------------------------------

def import_writer_bot_profile(
    user_id: int,
    data
):
    profiles = load_profiles()

    user_key = str(
        user_id
    )

    profile = profiles.get(
        user_key,
        {
            "xp": 0,
            "level": 0,
            "last_project_id": None,
            "imports": {}
        }
    )

    writer_level = data.get(
        "level"
    )
    writer_xp = data.get(
        "xp",
        0
    )

    if writer_level is not None:
        writer_level = max(
            1,
            int(writer_level)
        )
        profile["level"] = writer_level
        profile["xp"] = (
            writer_level - 1
        ) * 100
    else:
        profile["xp"] = int(writer_xp or 0)
        profile["level"] = calculate_level(
            profile["xp"]
        )

    imports = profile.get(
        "imports",
        {}
    )

    imports[
        "writer_bot"
    ] = {
        "imported_at": datetime.now().isoformat(),
        "stats": {
            "total_words": data.get(
                "total_words"
            ),
            "sprint_words": data.get(
                "sprint_words"
            ),
            "sprint_count": data.get(
                "sprint_count"
            ),
            "sprints_won": data.get(
                "sprints_won"
            ),
            "sprints_started": data.get(
                "sprints_started"
            ),
            "wins": data.get(
                "wins"
            ),
            "records": data.get(
                "records"
            ),
            "goals": data.get(
                "goals"
            )
        },
        "migration": {
            "legacy_xp": writer_xp,
            "legacy_level": writer_level,
            "sprint_words": data.get("sprint_words"),
            "sprint_count": data.get("sprint_count"),
            "sprints_won": data.get("sprints_won")
        },
        "raw": data
    }

    economy = profile.setdefault(
        "economy",
        {
            "coins": 0,
            "transactions": [],
            "migrations": {}
        }
    )
    migrations = economy.setdefault(
        "migrations",
        {}
    )
    if "writer_bot" not in migrations:
        sprint_words = int(data.get("sprint_words") or 0)
        sprint_count = int(data.get("sprint_count") or 0)
        sprints_won = int(data.get("sprints_won") or data.get("wins") or 0)
        converted_coins = (
            sprint_words // 1000
            + sprint_count // 10
            + sprints_won // 5
        )
        economy["coins"] = int(
            economy.get("coins", 0)
        ) + converted_coins
        economy["lifetime_xp"] = max(
            int(economy.get("lifetime_xp", 0)),
            int(profile["xp"])
        )
        economy.setdefault(
            "transactions",
            []
        ).append({
            "transaction_id": f"writer_bot:{user_id}",
            "user_id": user_id,
            "type": "writer_bot_migration",
            "amount": converted_coins,
            "balance_before": int(
                economy.get("coins", 0)
            ) - converted_coins,
            "balance_after": int(
                economy.get("coins", 0)
            ),
            "source": "writer_bot_migration",
            "related_id": user_id,
            "timestamp": datetime.now().timestamp()
        })
        migrations["writer_bot"] = {
            "converted_coins": converted_coins,
            "source_xp": writer_xp,
            "source_level": writer_level,
            "converted_at": datetime.now().isoformat()
        }

    profile["economy"] = economy
    profile["imports"] = imports

    profiles[
        user_key
    ] = profile

    save_profiles(
        profiles
    )

    return profile


# -------------------------------------------------------
#                    WRITER BOT IMPORT
# -------------------------------------------------------

def import_writer_bot(
    user_id: int,
    data
):
    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Writer Bot export must be a JSON object."
        )

    if "projects" not in data:
        raise ValueError(
            "This doesn't look like a Writer Bot export."
        )

    project_result = (
        import_writer_bot_projects(
            user_id=user_id,
            source_projects=data.get(
                "projects",
                []
            )
        )
    )

    import_writer_bot_profile(
        user_id=user_id,
        data=data
    )

    return project_result