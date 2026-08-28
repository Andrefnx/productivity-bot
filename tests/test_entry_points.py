import inspect
import unittest

import main


class EntryPointTests(unittest.TestCase):
    def test_config_uses_registry_menu_with_guild_context(self):
        source = inspect.getsource(main.config.callback)

        self.assertIn("ConfigMenuView(", source)
        self.assertIn("guild_id=interaction.guild_id", source)
        self.assertIn("Choose a settings category.", source)

    def test_help_uses_registry_view_with_guild_context(self):
        source = inspect.getsource(main.help_command.callback)

        self.assertIn("HelpView(", source)
        self.assertIn("guild_id=interaction.guild_id", source)


if __name__ == "__main__":
    unittest.main()