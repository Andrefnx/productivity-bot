import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import SprintView
from modules.sprints.system_messages import create_waiting_embed


class SprintCountdownTests(unittest.TestCase):
    def create_sprint(self, starts_in=10):
        return SprintView(
            duration=30,
            starts_in=starts_in,
            creator_id=111111111111111111,
            guild_id=222222222222222222,
            channel_id=333333333333333333,
            channel_config=DEFAULT_CHANNEL_CONFIG.copy(),
            sprint_config=DEFAULT_SPRINT_CONFIG.copy()
        )

    def test_waiting_embed_uses_discord_relative_timestamp(self):
        for starts_in in (10, 1):
            with patch("modules.sprints.active_sprint.time.time", return_value=1000):
                sprint = self.create_sprint(starts_in)

            embed = create_waiting_embed(
                duration=sprint.duration,
                start_timestamp=sprint.start_timestamp
            )
            starts_field = next(
                field
                for field in embed.fields
                if field.name == "Starts"
            )
            self.assertEqual(
                starts_field.value,
                f"<t:{1000 + starts_in * 60}:R>"
            )

    def test_change_time_updates_the_timestamp_source_of_truth(self):
        sprint = self.create_sprint(10)
        sprint.message = SimpleNamespace(edit=AsyncMock())

        with patch(
            "modules.sprints.active_sprint.time.time",
            return_value=2000
        ), patch(
            "modules.sprints.active_sprint.asyncio.create_task",
            side_effect=lambda coroutine: coroutine.close()
        ) as create_task:
            asyncio.run(sprint.restart_waiting_timer(30, 1))

        self.assertEqual(sprint.start_timestamp, 2060)
        starts_field = next(
            field
            for field in sprint.message.edit.await_args.kwargs["embed"].fields
            if field.name == "Starts"
        )
        self.assertEqual(starts_field.value, "<t:2060:R>")
        create_task.assert_called_once()

    def test_join_and_leave_refresh_keep_the_start_timestamp(self):
        sprint = self.create_sprint(10)
        original_timestamp = sprint.start_timestamp
        sprint.update_current_message = AsyncMock()
        user = SimpleNamespace(
            id=111111111111111111,
            display_name="Test User",
            mention="<@111111111111111111>"
        )
        interaction = SimpleNamespace(
            user=user,
            response=SimpleNamespace(send_message=AsyncMock())
        )
        project = {"project_id": "project", "name": "Project", "wordcount": 0}

        with patch("modules.sprints.users.set_last_project"):
            sprint.participants.add_user(user, project, 0)

        asyncio.run(sprint.leave.callback(interaction))

        self.assertEqual(sprint.start_timestamp, original_timestamp)
        sprint.update_current_message.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()