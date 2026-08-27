# -------------------------------------------------------
#                   SPRINT CONFIG DEFAULTS
# -------------------------------------------------------

DEFAULT_SPRINT_CONFIG = {
	"allow_join_after_start": None,
	"allow_leave_after_start": None,
	"allow_change_duration_after_start": None,
	"allow_change_waiting_time": None,
	"empty_sprint_timeout": None
}


# -------------------------------------------------------
#                   SPRINT CONFIG DATA
# -------------------------------------------------------

def create_sprint_config(
	overrides=None
):
	config = DEFAULT_SPRINT_CONFIG.copy()

	if overrides:
		unknown_keys = set(overrides) - set(config)
		if unknown_keys:
			raise KeyError(
				f"Unknown sprint config keys: {unknown_keys}"
			)

		config.update(
			overrides
		)

	return config


def set_sprint_override(
	config,
	key,
	value
):
	if key not in DEFAULT_SPRINT_CONFIG:
		raise KeyError(
			f"Unknown sprint config key: {key}"
		)

	if value not in (
		None,
		True,
		False
	) and key != "empty_sprint_timeout":
		raise ValueError(
			f"Invalid override for {key}: {value}"
		)

	if key == "empty_sprint_timeout" and (
		value is not None
		and (
			isinstance(value, bool)
			or
			not isinstance(value, int)
			or value < 0
		)
	):
		raise ValueError(
			f"Invalid override for {key}: {value}"
		)

	config[key] = value
	return config


__all__ = [
	"DEFAULT_SPRINT_CONFIG",
	"create_sprint_config"
	,"set_sprint_override"
]