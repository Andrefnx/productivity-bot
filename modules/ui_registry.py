from importlib import import_module
from pathlib import Path

import modules

from modules.common.ui.registry import UIRegistry


MODULES_ROOT = Path(modules.__file__).resolve().parent


def _iter_module_contributors(filename, register_name):
    for path in sorted(MODULES_ROOT.rglob(filename)):
        if "__pycache__" in path.parts:
            continue

        relative = path.relative_to(MODULES_ROOT).with_suffix("")
        module_name = "modules." + ".".join(relative.parts)
        module = import_module(module_name)
        register = getattr(module, register_name, None)

        if register is not None:
            yield register


def get_help_registry():
    registry = UIRegistry("help")

    from modules.help.help_entries import register_help as register_general_help

    register_general_help(registry)

    for register in _iter_module_contributors("help.py", "register_help"):
        register(registry)

    return registry


def get_settings_registry():
    registry = UIRegistry("settings")

    for register in _iter_module_contributors("settings.py", "register_settings"):
        register(registry)

    return registry
