import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import SprintView


class EmptyActiveSprintTests(unittest.TestCase):
    def create_sprint(self, started=True):
        sprint = SprintView(
            duration=30,
            starts_in=5,
            creator_id=111111111111111111,
            guild_id=222222222222222222,
            channel_id=333333333333333333,
            channel_config=DEFAULT_CHANNEL_CONFIG.copy(),
            sprint_config=DEFAULT_SPRINT_CONFIG.copy()
        )
        sprint.started = started
        return sprint

    def test_active_empty_sprint_starts_one_grace_task(self):
        sprint = self.create_sprint()
        task = MagicMock()
        with patch(
            "modules.sprints.active_sprint.asyncio.create_task",
            side_effect=lambda coroutine: (
                coroutine.close(),
                task
            )[1]
        ) as create_task:
            sprint.participant_left()
            sprint.participant_left()

        create_task.assert_called_once()
        self.assertIs(sprint.empty_sprint_timer, task)

    def test_join_cancels_pending_empty_grace_task(self):
        sprint = self.create_sprint()
        task = MagicMock()
        sprint.empty_sprint_timer = task

        sprint.participant_joined()

        task.cancel.assert_called_once()
        self.assertIsNone(sprint.empty_sprint_timer)

    def test_new_leave_after_join_creates_new_grace_task(self):
        sprint = self.create_sprint()
        first_task = MagicMock()
        second_task = MagicMock()
        sprint.empty_sprint_timer = first_task
        sprint.participant_joined()

        with patch(
            "modules.sprints.active_sprint.asyncio.create_task",
            side_effect=lambda coroutine: (
                coroutine.close(),
                second_task
            )[1]
        ) as create_task:
            sprint.participant_left()

        first_task.cancel.assert_called_once()
        create_task.assert_called_once()
        self.assertIs(sprint.empty_sprint_timer, second_task)

    def test_empty_timeout_cancels_only_active_empty_sprint(self):
        sprint = self.create_sprint()
        sprint.close_empty_sprint = AsyncMock()
        with patch(
            "modules.sprints.active_sprint.asyncio.sleep",
            new=AsyncMock()
        ):
            asyncio.run(sprint.wait_for_empty_sprint_timeout())

        sprint.close_empty_sprint.assert_awaited_once()

    def test_empty_timeout_does_not_cancel_after_join_or_finish(self):
        for participants, finished in ((1, False), (0, True)):
            sprint = self.create_sprint()
            sprint.finished = finished
            sprint.close_empty_sprint = AsyncMock()
            if participants:
                sprint.participants.users[1] = SimpleNamespace()
            with patch(
                "modules.sprints.active_sprint.asyncio.sleep",
                new=AsyncMock()
            ):
                asyncio.run(sprint.wait_for_empty_sprint_timeout())
            sprint.close_empty_sprint.assert_not_awaited()

    def test_waiting_empty_sprint_does_not_start_grace_task(self):
        sprint = self.create_sprint(started=False)
        with patch(
            "modules.sprints.active_sprint.asyncio.create_task"
        ) as create_task:
            sprint.participant_left()
        create_task.assert_not_called()

    def test_manual_cancel_cancels_pending_empty_task(self):
        sprint = self.create_sprint()
        sprint.empty_sprint_timer = MagicMock()
        sprint.sprint_timer = MagicMock()
        sprint.message = SimpleNamespace(edit=AsyncMock(), id=1)
        interaction = SimpleNamespace(
            user=SimpleNamespace(id=sprint.creator_id, mention="@creator"),
            response=SimpleNamespace(edit_message=AsyncMock())
        )
        with patch(
            "modules.sprints.active_sprint.get_channel_config",
            return_value=DEFAULT_CHANNEL_CONFIG.copy()
        ), patch(
            "modules.sprints.active_sprint.update_active_sprint_status"
        ):
            asyncio.run(sprint.confirm_cancel(interaction))
        self.assertTrue(sprint.finished)
        self.assertIsNone(sprint.empty_sprint_timer)


if __name__ == "__main__":
    unittest.main()