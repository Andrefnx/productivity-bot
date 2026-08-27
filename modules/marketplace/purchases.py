import asyncio
from copy import deepcopy
import time
import uuid

from modules.economy import (
    can_afford,
    get_level,
    spend_coins
)

from .market_data import (
    get_inventory,
    load_data,
    save_data,
    update_inventory
)
from .server_rewards import get_server_reward
from .market_data import load_marketplace_config


# -------------------------------------------------------
#                 PURCHASE OPERATIONS
# -------------------------------------------------------

_purchase_lock = asyncio.Lock()


async def purchase_server_reward(user_id, reward_id, guild_id=None, confirmation_token=None):
    async with _purchase_lock:
        reward = get_server_reward(reward_id)
        if reward is None or not reward["enabled"]:
            return False, "This reward is unavailable."
        config = load_marketplace_config(
            guild_id
        )
        data = load_data("purchases")
        if confirmation_token:
            for purchase in data.values():
                if purchase.get("confirmation_token") == confirmation_token:
                    return True, purchase["purchase_id"]
        if not config["marketplace_enabled"]:
            return False, "Marketplace is disabled in this server."
        required_level = max(
            config["minimum_purchase_level"],
            reward["required_level"]
        )
        if get_level(user_id) < required_level:
            return False, f"Requires Level {required_level}."
        if not can_afford(user_id, reward["price"]):
            return False, "You do not have enough coins."
        from modules.user_profile.profile_storage import (
            load_profiles,
            save_profiles
        )

        profiles_before = load_profiles()
        inventory_before = deepcopy(
            get_inventory(user_id)
        )
        data_before = deepcopy(data)
        if not spend_coins(user_id, reward["price"], "market_purchase", reward_id):
            return False, "Your coin balance changed. Try again."
        try:
            inventory = get_inventory(user_id)
            inventory[reward_id] = inventory.get(reward_id, 0) + 1
            update_inventory(user_id, inventory)
            purchase_id = str(uuid.uuid4())
            data[purchase_id] = {
                "purchase_id": purchase_id,
                "reward_id": reward_id,
                "type": "server_reward",
                "buyer_id": user_id,
                "price": reward["price"],
                "status": "completed",
                "confirmation_token": confirmation_token,
                "created_at": time.time(),
                "updated_at": time.time()
            }
            save_data("purchases", data)
            return True, purchase_id
        except (OSError, TypeError, ValueError):
            save_profiles(profiles_before)
            update_inventory(user_id, inventory_before)
            save_data("purchases", data_before)
            return False, "The purchase could not be saved. No coins were charged."
