import logging
import os


FEATURE_BOT_CUSTOMIZATION = "bot_customization"

FEATURES = {
    FEATURE_BOT_CUSTOMIZATION: {
        "tier": "premium"
    }
}


def get_premium_guild_ids():
    guild_ids = set()
    raw_ids = os.getenv("PREMIUM_GUILD_IDS", "")

    for value in raw_ids.split(","):
        guild_id = value.strip()

        if not guild_id:
            continue

        if not guild_id.isdigit():
            logging.warning(
                "Ignoring invalid PREMIUM_GUILD_IDS value: %r",
                guild_id
            )
            continue

        guild_ids.add(guild_id)

    return guild_ids


def is_premium_guild(guild_id):
    if guild_id is None:
        return False

    return str(guild_id) in get_premium_guild_ids()


def is_feature_enabled(feature_key, guild_id):
    feature = FEATURES.get(feature_key)

    if feature is None:
        return False

    if feature["tier"] == "premium":
        return is_premium_guild(guild_id)

    return True