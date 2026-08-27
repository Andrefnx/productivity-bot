from .config_data import get_user_config


# -------------------------------------------------------
#                 DISCORD PERMISSIONS
# -------------------------------------------------------

def can_edit_channel_config(
	member
):
	permissions = getattr(
		member,
		"guild_permissions",
		None
	)

	return bool(
		permissions
		and (
			permissions.administrator
			or permissions.manage_guild
		)
	)


# -------------------------------------------------------
#                  SPRINT PERMISSIONS
# -------------------------------------------------------

def _permissions(member):
	return getattr(
		member,
		"guild_permissions",
		None
	)


def is_administrator(
	member
):
	permissions = _permissions(
		member
	)
	return bool(
		permissions
		and permissions.administrator
	)


def is_moderator(
	member
):
	permissions = _permissions(
		member
	)
	return bool(
		permissions
		and (
			permissions.administrator
			or permissions.manage_guild
			or permissions.manage_messages
		)
	)


def can_create_sprint(
	member,
	setting
):
	if is_administrator(member):
		return True

	if setting == "everyone":
		return True

	if setting == "manage_messages":
		permissions = _permissions(member)
		return bool(
			permissions
			and permissions.manage_messages
		)

	return False


def can_manage_sprint_action(
	member,
	creator_id,
	setting
):
	if is_administrator(member):
		return True

	if setting == "creator":
		return member.id == creator_id

	if setting == "creator_or_moderator":
		return (
			member.id == creator_id
			or is_moderator(member)
		)

	return False


def can_edit_sprint_settings(
	member,
	creator_id
):
	return (
		member.id == creator_id
		or is_moderator(member)
	)


def can_view_profile(
	owner,
	viewer,
	guild=None
):
	if owner.id == viewer.id:
		return True

	config = get_user_config(
		owner.id
	)

	return config[
		"profile_visibility"
	] == "public"


def can_view_projects(
	owner,
	viewer,
	guild=None
):
	if owner.id == viewer.id:
		return True

	config = get_user_config(
		owner.id
	)

	return config[
		"projects_visibility"
	] == "public"


# -------------------------------------------------------
#                 SETTINGS RESOLUTION
# -------------------------------------------------------

def resolve_sprint_setting(
	key,
	channel_config,
	sprint_config
):
	channel_value = channel_config.get(key)
	sprint_value = sprint_config.get(key)

	if sprint_value is None:
		return channel_value

	if isinstance(channel_value, bool):
		return channel_value and sprint_value

	return sprint_value


def resolve_sprint_config(
	channel_config,
	sprint_config
):
	keys = set(channel_config) | set(sprint_config)

	return {
		key: resolve_sprint_setting(
			key,
			channel_config,
			sprint_config
		)
		for key in keys
	}


def resolve_empty_sprint_timeout(
    channel_config,
    sprint_config
):
	channel_timeout = channel_config.get(
		"empty_sprint_timeout"
	)
	sprint_timeout = sprint_config.get(
		"empty_sprint_timeout"
	)

	if sprint_timeout is None:
		return channel_timeout * 60

	return min(
		channel_timeout * 60,
		sprint_timeout
	)


def resolve_setting(
	key,
	user_config=None,
	channel_config=None,
	sprint_config=None
):
	user_config = user_config or {}
	channel_config = channel_config or {}
	sprint_config = sprint_config or {}

	value = user_config.get(
		key
	)

	if key in channel_config:
		value = channel_config[key]

	if key in sprint_config and sprint_config[key] is not None:
		if isinstance(value, bool):
			value = value and sprint_config[key]
		else:
			value = sprint_config[key]

	return value
