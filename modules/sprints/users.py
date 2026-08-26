import json
import os

import discord


# -------------------------------------------------------
#                    USER STORAGE
# -------------------------------------------------------

DATA_DIRECTORY = "data"

SPRINT_USERS_FILE = os.path.join(
    DATA_DIRECTORY,
    "sprint_users.json"
)


def load_sprint_users():
    if not os.path.exists(
        SPRINT_USERS_FILE
    ):
        return {}

    try:
        with open(
            SPRINT_USERS_FILE,
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


def save_sprint_users(
    users
):
    os.makedirs(
        DATA_DIRECTORY,
        exist_ok=True
    )

    with open(
        SPRINT_USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            users,
            file,
            indent=4
        )


def save_previous_sprint_data(
    user_id: int,
    initial_wc,
    project
):
    users = load_sprint_users()

    users[str(user_id)] = {
        "initial_wc": initial_wc,
        "project": project
    }

    save_sprint_users(
        users
    )


def get_previous_sprint_data(
    user_id: int
):
    users = load_sprint_users()

    return users.get(
        str(user_id)
    )


# -------------------------------------------------------
#                     SPRINT USER
# -------------------------------------------------------

class SprintUser:
    def __init__(
        self,
        user: discord.User | discord.Member,
        initial_wc=None,
        project=None
    ):
        self.id = user.id
        self.user = user

        self.initial_wc = initial_wc
        self.final_wc = None

        self.project = (
            project.strip()
            if project
            else None
        )

    @property
    def mention(
        self
    ):
        return f"<@{self.id}>"

    def get_display_text(
        self
    ):
        if self.initial_wc is None:
            wordcount = "no wordcount"

        else:
            wordcount = (
                f"{self.initial_wc} words"
            )

        project = (
            self.project
            if self.project
            else "no project"
        )

        return (
            f"{self.mention} - "
            f"{wordcount} - "
            f"{project}"
        )


# -------------------------------------------------------
#                  SPRINT PARTICIPANTS
# -------------------------------------------------------

class SprintParticipants:
    def __init__(
        self
    ):
        self.users = {}

    def add_user(
        self,
        user: discord.User | discord.Member,
        initial_wc=None,
        project=None
    ):
        if user.id in self.users:
            return False

        sprint_user = SprintUser(
            user=user,
            initial_wc=initial_wc,
            project=project
        )

        self.users[user.id] = sprint_user

        save_previous_sprint_data(
            user_id=user.id,
            initial_wc=initial_wc,
            project=project
        )

        return True

    def remove_user(
        self,
        user_id: int
    ):
        if user_id not in self.users:
            return False

        del self.users[user_id]

        return True

    def has_user(
        self,
        user_id: int
    ):
        return user_id in self.users

    def get_user(
        self,
        user_id: int
    ):
        return self.users.get(
            user_id
        )

    def get_mentions(
        self
    ):
        return [
            sprint_user.mention
            for sprint_user
            in self.users.values()
        ]

    def get_mentions_text(
        self
    ):
        if not self.users:
            return "No participants yet."

        return "\n".join(
            sprint_user.get_display_text()
            for sprint_user
            in self.users.values()
        )

    def get_start_ping(
        self
    ):
        mentions = self.get_mentions()

        if not mentions:
            return None

        return " ".join(
            mentions
        )

    def __len__(
        self
    ):
        return len(
            self.users
        )