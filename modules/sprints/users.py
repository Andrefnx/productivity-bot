import discord


# -------------------------------------------------------
#                     SPRINT USER
# -------------------------------------------------------

class SprintUser:
    def __init__(
        self,
        user: discord.User | discord.Member
    ):
        self.id = user.id
        self.user = user

        self.initial_wc = None
        self.final_wc = None

    @property
    def mention(self):
        return f"<@{self.id}>"


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
        user: discord.User | discord.Member
    ):
        if user.id in self.users:
            return False

        self.users[user.id] = SprintUser(
            user
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
        mentions = self.get_mentions()

        if not mentions:
            return "No participants yet."

        return "\n".join(
            mentions
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