import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.config.channel.channel_config import DEFAULT_CHANNEL_CONFIG
from modules.config.sprint.sprint_config import DEFAULT_SPRINT_CONFIG
from modules.sprints.active_sprint import SprintView
from modules.sprints.system_messages import (
    normalize_sprint_status,
    recover_old_sprints,
    recover_saved_sprints
)


class SprintLifecycleRecoveryTests(unittest.TestCase):
    def test_legacy_statuses_map_to_canonical_lifecycle(self):
        expected = {
            "scheduled": "countdown",
            "waiting": "countdown",
            "running": "active",
            "started": "active",
            "finished": "completed",
            "complete": "completed",
            "ended": "completed",
            "canceled": "cancelled",
            "aborted": "interrupted"
        }

        for legacy, canonical in expected.items():
            self.assertEqual(normalize_sprint_status(legacy), canonical)

    def test_normal_completion_persists_before_results_and_edits_message(self):
        sprint = SprintView(
            duration=30,
            starts_in=0,
            creator_id=1,
            guild_id=2,
            channel_id=3,
            channel_config=DEFAULT_CHANNEL_CONFIG.copy(),
            sprint_config=DEFAULT_SPRINT_CONFIG.copy()
        )
        sprint.started = True
        sprint.end_timestamp = 2000
        user = SimpleNamespace(id=1, mention="<@1>", display_name="User")
        sprint.participants.add_user(user)
        sprint.message = SimpleNamespace(
            id=10,
            channel=SimpleNamespace(),
            edit=AsyncMock()
        )

        with patch(
            "modules.sprints.active_sprint.update_active_sprint_status"
        ) as update_status, patch(
            "modules.sprints.active_sprint.start_results_registration",
            new=AsyncMock()
        ):
            asyncio.run(sprint.finish_sprint())

        self.assertEqual(update_status.call_args.args[1], "completed")
        self.assertEqual(
            sprint.message.edit.await_args.kwargs["embed"].title,
            "Sprint finished!"
        )

    def test_active_sprint_before_end_is_interrupted_on_recovery(self):
        message = SimpleNamespace(
            embeds=[],
            edit=AsyncMock()
        )
        channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message))
        client = SimpleNamespace(get_channel=lambda channel_id: channel)
        records = [{
            "guild_id": 1,
            "channel_id": 2,
            "message_id": 3,
            "status": "active",
            "end_timestamp": 2000
        }]

        with patch(
            "modules.sprints.system_messages.load_active_sprints",
            return_value=records
        ), patch(
            "modules.sprints.system_messages.save_active_sprints"
        ), patch(
            "modules.sprints.system_messages.time.time",
            return_value=1000
        ):
            asyncio.run(recover_saved_sprints(client))

        self.assertEqual(message.edit.await_args.kwargs["embed"].title, "🛠️ Bot out of order")
        self.assertEqual(records[0]["status"], "interrupted")

    def test_stale_active_sprint_after_end_becomes_completed(self):
        message = SimpleNamespace(embeds=[], edit=AsyncMock())
        channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message))
        client = SimpleNamespace(get_channel=lambda channel_id: channel)
        records = [{
            "guild_id": 1,
            "channel_id": 2,
            "message_id": 3,
            "status": "active",
            "end_timestamp": 1000
        }]

        with patch(
            "modules.sprints.system_messages.load_active_sprints",
            return_value=records
        ), patch(
            "modules.sprints.system_messages.save_active_sprints"
        ), patch(
            "modules.sprints.system_messages.time.time",
            return_value=2000
        ):
            asyncio.run(recover_saved_sprints(client))

        self.assertEqual(message.edit.await_args.kwargs["embed"].title, "Sprint finished!")
        self.assertEqual(records[0]["status"], "completed")

    def test_terminal_records_are_not_overwritten_during_recovery(self):
        for status in ("completed", "cancelled"):
            message = SimpleNamespace(embeds=[], edit=AsyncMock())
            channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message))
            client = SimpleNamespace(get_channel=lambda channel_id: channel)
            records = [{"channel_id": 2, "message_id": 3, "status": status}]

            with patch(
                "modules.sprints.system_messages.load_active_sprints",
                return_value=records
            ), patch(
                "modules.sprints.system_messages.save_active_sprints"
            ):
                asyncio.run(recover_saved_sprints(client))

            message.edit.assert_not_awaited()

    def test_history_recovery_finishes_expired_started_message(self):
        embed = SimpleNamespace(
            title="Sprint started!",
            description="Ends <t:1000:R>.",
            fields=[]
        )
        message = SimpleNamespace(
            author=SimpleNamespace(id=1),
            embeds=[embed],
            components=[SimpleNamespace()],
            edit=AsyncMock()
        )

        async def history(limit):
            yield message

        channel = SimpleNamespace(history=history)
        client = SimpleNamespace(
            user=SimpleNamespace(id=1),
            guilds=[SimpleNamespace(text_channels=[channel])]
        )

        with patch(
            "modules.sprints.system_messages.time.time",
            return_value=2000
        ):
            asyncio.run(recover_old_sprints(client))

        self.assertEqual(message.edit.await_args.kwargs["embed"].title, "Sprint finished!")


if __name__ == "__main__":
    unittest.main()