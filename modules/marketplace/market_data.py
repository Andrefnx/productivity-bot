import json
from pathlib import Path


# -------------------------------------------------------
#                 MARKETPLACE STORAGE
# -------------------------------------------------------

DATA_PATH = Path(__file__).resolve().parents[2] / "data"
FILES = {
    "offers": DATA_PATH / "marketplace_offers.json",
    "purchases": DATA_PATH / "marketplace_purchases.json",
    "inventory": DATA_PATH / "marketplace_inventory.json",
    "rewards": DATA_PATH / "marketplace_rewards.json",
    "config": DATA_PATH / "marketplace_config.json",
    "rooms": DATA_PATH / "marketplace_rooms.json",
    "transactions": DATA_PATH / "marketplace_transactions.json"
}


# -------------------------------------------------------
#                 MARKETPLACE STORAGE
# -------------------------------------------------------

def load_marketplace_config(guild_id):
    data = load_data("config")
    config = {
        "marketplace_enabled": True,
        "minimum_purchase_level": 3,
        "minimum_seller_level": 10,
        "user_offers_enabled": True,
        "user_offer_coin_transfers_enabled": True
    }
    config.update(data.get(str(guild_id), {}))
    config["minimum_purchase_level"] = max(
        3,
        int(config["minimum_purchase_level"])
    )
    config["minimum_seller_level"] = max(
        10,
        int(config["minimum_seller_level"])
    )
    return config


def get_marketplace_config(guild_id):
    return load_marketplace_config(guild_id)


def save_marketplace_config(guild_id, config):
    data = load_data("config")
    data[str(guild_id)] = config
    save_data("config", data)


def update_marketplace_config(guild_id, key, value):
    config = load_marketplace_config(guild_id)
    if key not in config:
        raise KeyError(f"Unknown marketplace setting: {key}")
    if key in ("minimum_purchase_level", "minimum_seller_level"):
        value = int(value)
        if value < 0:
            raise ValueError("Level cannot be negative.")
    config[key] = value
    save_marketplace_config(guild_id, config)
    return config


def load_data(name):
    path = FILES[name]
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_data(name, data):
    path = FILES[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def get_inventory(user_id):
    data = load_data("inventory")
    return data.get(str(user_id), {})


def update_inventory(user_id, inventory):
    data = load_data("inventory")
    data[str(user_id)] = inventory
    save_data("inventory", data)
    return inventory
