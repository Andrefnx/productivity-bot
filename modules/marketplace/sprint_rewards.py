from .market_data import get_inventory, update_inventory


def get_entitlement_count(user_id, reward_id):
    return int(get_inventory(user_id).get(reward_id, 0))


def consume_entitlement(user_id, reward_id):
    inventory = get_inventory(user_id)
    count = int(inventory.get(reward_id, 0))
    if count <= 0:
        return False
    inventory[reward_id] = count - 1
    update_inventory(user_id, inventory)
    return True