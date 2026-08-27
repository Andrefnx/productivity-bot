from modules.economy import get_level

from .market_data import load_marketplace_config


def can_purchase(user_id, required_level):
    return get_level(user_id) >= required_level


def can_sell(user_id, guild_id=None):
    minimum_level = 10
    if guild_id is not None:
        minimum_level = load_marketplace_config(
            guild_id
        )["minimum_seller_level"]
    return get_level(user_id) >= max(10, minimum_level)


def can_manage_marketplace(member):
    permissions = getattr(member, "guild_permissions", None)
    return bool(
        permissions
        and (
            permissions.administrator
            or permissions.manage_guild
        )
    )
