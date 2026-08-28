import os
import unittest
from unittest.mock import patch

from modules.common.entitlements import (
    FEATURE_BOT_CUSTOMIZATION,
    get_premium_guild_ids,
    is_feature_enabled,
    is_premium_guild
)


class EntitlementTests(unittest.TestCase):
    def test_missing_premium_guild_ids_returns_empty_set(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_premium_guild_ids(), set())

    def test_parses_single_and_multiple_guild_ids(self):
        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111,222,333"},
            clear=True
        ):
            self.assertEqual(
                get_premium_guild_ids(),
                {"111", "222", "333"}
            )

    def test_ignores_spaces_empty_values_and_invalid_ids(self):
        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": " 111, , invalid, 222 ,,"},
            clear=True
        ):
            with self.assertLogs(level="WARNING"):
                self.assertEqual(
                    get_premium_guild_ids(),
                    {"111", "222"}
                )

    def test_premium_feature_requires_premium_guild(self):
        with patch.dict(
            os.environ,
            {"PREMIUM_GUILD_IDS": "111"},
            clear=True
        ):
            self.assertTrue(
                is_feature_enabled(FEATURE_BOT_CUSTOMIZATION, 111)
            )
            self.assertFalse(
                is_feature_enabled(FEATURE_BOT_CUSTOMIZATION, 222)
            )
            self.assertFalse(
                is_feature_enabled(FEATURE_BOT_CUSTOMIZATION, None)
            )
            self.assertTrue(is_premium_guild("111"))

    def test_unknown_feature_is_disabled(self):
        self.assertFalse(is_feature_enabled("unknown", 111))


if __name__ == "__main__":
    unittest.main()