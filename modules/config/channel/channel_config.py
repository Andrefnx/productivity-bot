import json

from pathlib import Path


# -------------------------------------------------------
#                  CHANNEL CONFIG DEFAULTS
# -------------------------------------------------------

DEFAULT_CHANNEL_CONFIG = {
	"create_sprints": "everyone",
	"cancel_sprints": "creator_or_moderator",
	"change_sprint_time": "creator_or_moderator",
	"allow_join_after_start": True,
	"allow_leave_after_start": True,
	"allow_change_duration_after_start": False,
	"allow_change_waiting_time": True,
	"default_duration": 30,
	"min_duration": 1,
	"max_duration": 180,
	"default_waiting_time": 10,
	"max_waiting_time": 30,
	"cancel_empty_sprints": True,
	"empty_sprint_timeout": 10
}

CHANNEL_CONFIG_PATH = (
	Path(__file__).resolve().parents[3]
	/ "data"
	/ "channel_config.json"
)


# -------------------------------------------------------
#                  CHANNEL CONFIG DATA
# -------------------------------------------------------

def _load_channel_configs():
	if not CHANNEL_CONFIG_PATH.exists():
		return {}

	with CHANNEL_CONFIG_PATH.open(
		"r",
		encoding="utf-8"
	) as config_file:
		return json.load(config_file)


def _save_channel_configs(configs):
	CHANNEL_CONFIG_PATH.parent.mkdir(
		parents=True,
		exist_ok=True
	)

	with CHANNEL_CONFIG_PATH.open(
		"w",
		encoding="utf-8"
	) as config_file:
		json.dump(
			configs,
			config_file,
			indent=4,
			sort_keys=True
		)


def get_channel_config(
	guild_id: int,
	channel_id: int
):
	configs = _load_channel_configs()
	guild_config = configs.get(
		str(guild_id),
		{}
	)
	saved_config = guild_config.get(
		str(channel_id),
		{}
	)

	config = DEFAULT_CHANNEL_CONFIG.copy()
	config.update(
		saved_config
	)

	return config


def update_channel_config(
	guild_id: int,
	channel_id: int,
	key: str,
	value
):
	if key not in DEFAULT_CHANNEL_CONFIG:
		raise KeyError(
			f"Unknown channel config key: {key}"
		)

	configs = _load_channel_configs()
	guild_key = str(guild_id)
	channel_key = str(channel_id)
	guild_config = configs.setdefault(
		guild_key,
		{}
	)
	saved_config = guild_config.setdefault(
		channel_key,
		{}
	)
	saved_config[key] = value

	_save_channel_configs(
		configs
	)

	return get_channel_config(
		guild_id,
		channel_id
	)


__all__ = [
	"DEFAULT_CHANNEL_CONFIG",
	"get_channel_config",
	"update_channel_config"
]