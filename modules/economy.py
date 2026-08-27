import asyncio
import time
import uuid

# -------------------------------------------------------
#                    ECONOMY DEFAULTS
# -------------------------------------------------------

XP_PER_LEVEL = 100
DEFAULT_COINS = 0
DEFAULT_ECONOMY = {
    "coins": 0,
    "lifetime_xp": 0,
    "lifetime_coins": 0,
    "sprints_rewarded": 0,
    "transactions": [],
    "migrations": {},
    "sprint_rewards": {}
}

_economy_lock = asyncio.Lock()


# -------------------------------------------------------
#                    LEVEL HELPERS
# -------------------------------------------------------

def calculate_level(xp: int):
    return (max(0, int(xp)) // XP_PER_LEVEL) + 1


def get_xp_progress(xp: int):
    return max(0, int(xp)) % XP_PER_LEVEL


# -------------------------------------------------------
#                    WALLET OPERATIONS
# -------------------------------------------------------

def get_economy(user_id: int):
    from modules.user_profile.profile_storage import get_profile, update_profile

    profile = get_profile(user_id)
    economy = profile.setdefault("economy", {})
    for key, value in DEFAULT_ECONOMY.items():
        economy.setdefault(
            key,
            value.copy() if isinstance(value, (dict, list)) else value
        )
    return economy


def get_coins(user_id: int):
    return int(get_economy(user_id).get("coins", DEFAULT_COINS))


def get_level(user_id: int):
    from modules.user_profile.profile_storage import get_profile

    return calculate_level(
        get_profile(user_id).get("xp", 0)
    )


def can_afford(user_id: int, amount: int):
    return amount >= 0 and get_coins(user_id) >= amount


def _record_transaction(user_id, transaction_type, amount, balance_before, balance_after, source, related_id=None):
    from modules.user_profile.profile_storage import update_profile

    economy = get_economy(user_id)
    economy["transactions"].append({
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": transaction_type,
        "amount": amount,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "source": source,
        "related_id": related_id,
        "timestamp": time.time()
    })
    update_profile(user_id, {"economy": economy})


def spend_coins(user_id: int, amount: int, source: str, related_id=None):
    from modules.user_profile.profile_storage import update_profile

    amount = int(amount)
    if amount < 0 or not can_afford(user_id, amount):
        return False
    economy = get_economy(user_id)
    balance_before = get_coins(user_id)
    economy["coins"] = balance_before - amount
    update_profile(user_id, {"economy": economy})
    _record_transaction(user_id, "market_purchase", -amount, balance_before, economy["coins"], source, related_id)
    return True


def credit_coins(user_id: int, amount: int, source: str, related_id=None):
    from modules.user_profile.profile_storage import update_profile

    amount = int(amount)
    if amount < 0:
        return False
    economy = get_economy(user_id)
    balance_before = get_coins(user_id)
    economy["coins"] = balance_before + amount
    economy["lifetime_coins"] = int(
        economy.get("lifetime_coins", 0)
    ) + amount
    update_profile(user_id, {"economy": economy})
    _record_transaction(user_id, "market_sale", amount, balance_before, economy["coins"], source, related_id)
    return True


def transfer_coins(buyer_id: int, seller_id: int, amount: int, related_id=None):
    async def transfer():
        async with _economy_lock:
            if buyer_id == seller_id or not can_afford(buyer_id, amount):
                return False
            if not spend_coins(buyer_id, amount, "market_sale", related_id):
                return False
            if not credit_coins(seller_id, amount, "market_sale", related_id):
                credit_coins(buyer_id, amount, "market_refund", related_id)
                return False
            return True
    return transfer()


def award_xp(user_id: int, amount: int, source="sprint", related_id=None):
    from modules.user_profile.profile_storage import (
        get_profile,
        update_profile
    )

    if amount <= 0:
        return get_profile(user_id)
    profile = get_profile(user_id)
    xp = int(profile.get("xp", 0)) + int(amount)
    economy = get_economy(user_id)
    economy["lifetime_xp"] = int(
        economy.get("lifetime_xp", 0)
    ) + int(amount)
    profile = update_profile(user_id, {
        "xp": xp,
        "level": calculate_level(xp),
        "economy": economy
    })
    return profile


# -------------------------------------------------------
#                    SPRINT REWARDS
# -------------------------------------------------------

def award_sprint_result(
    sprint_user,
    duration,
    sprint_id
):
    from modules.user_profile.profile_storage import get_profile, update_profile

    profile = get_profile(
        sprint_user.user_id
    )
    economy = get_economy(
        sprint_user.user_id
    )
    rewards = economy.setdefault(
        "sprint_rewards",
        {}
    )
    reward_key = f"{sprint_id}:{sprint_user.user_id}"

    if reward_key in rewards:
        return False

    words = sprint_user.words_written
    duration = max(0, int(duration))
    if duration < 15:
        duration_xp = 0
    elif duration < 30:
        duration_xp = 2
    elif duration < 60:
        duration_xp = 5
    elif duration < 120:
        duration_xp = 10
    else:
        duration_xp = 15

    if words is None:
        xp = 10
        coins = 0
    else:
        positive_words = max(
            0,
            int(words)
        )
        xp = 15 + duration_xp + positive_words // 50
        coins = max(
            1,
            positive_words // 100
        )

    current_xp = int(profile.get("xp", 0))
    new_xp = current_xp + xp
    economy["coins"] = get_coins(
        sprint_user.user_id
    ) + coins
    economy["lifetime_xp"] = int(
        economy.get("lifetime_xp", 0)
    ) + xp
    economy["lifetime_coins"] = int(
        economy.get("lifetime_coins", 0)
    ) + coins
    economy["sprints_rewarded"] = int(
        economy.get("sprints_rewarded", 0)
    ) + 1
    rewards[reward_key] = {
        "xp": xp,
        "coins": coins,
        "sprint_id": sprint_id,
        "timestamp": time.time()
    }
    update_profile(
        sprint_user.user_id,
        {
            "xp": new_xp,
            "level": calculate_level(new_xp),
            "economy": economy
        }
    )
    return True
