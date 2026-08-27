import asyncio
from copy import deepcopy
import time
import uuid

from modules.economy import (
    can_afford,
    get_level,
    transfer_coins
)

from .market_data import load_data, save_data
from .market_data import load_marketplace_config


# -------------------------------------------------------
#                    OFFER OPERATIONS
# -------------------------------------------------------

_offer_lock = asyncio.Lock()


def list_offers(guild_id, include_unavailable=False):
    offers = load_data("offers")
    values = [offer for offer in offers.values() if offer.get("guild_id") == guild_id]
    if not include_unavailable:
        values = [offer for offer in values if offer.get("status") == "available" and offer.get("remaining_quantity", 0) > 0]
    return sorted(values, key=lambda offer: offer.get("created_at", 0), reverse=True)


def create_offer(seller_id, guild_id, name, description, price, minimum_buyer_level, quantity):
    config = load_marketplace_config(guild_id)
    if not config["user_offers_enabled"]:
        return None
    if get_level(seller_id) < max(10, config["minimum_seller_level"]) or not name.strip() or not description.strip() or price <= 0 or quantity <= 0:
        return None
    data = load_data("offers")
    offer_id = str(uuid.uuid4())
    data[offer_id] = {
        "offer_id": offer_id,
        "seller_id": seller_id,
        "guild_id": guild_id,
        "name": name.strip()[:100],
        "description": description.strip()[:500],
        "price": int(price),
        "minimum_buyer_level": max(3, int(minimum_buyer_level)),
        "quantity": int(quantity),
        "remaining_quantity": int(quantity),
        "status": "available",
        "created_at": time.time(),
        "updated_at": time.time()
    }
    save_data("offers", data)
    return data[offer_id]


async def purchase_offer(buyer_id, offer_id, confirmation_token=None):
    async with _offer_lock:
        offers = load_data("offers")
        offer = offers.get(offer_id)
        if offer:
            config = load_marketplace_config(offer["guild_id"])
        else:
            config = None
        if config and not config["marketplace_enabled"]:
            return False, "Marketplace is disabled in this server."
        if config and not config["user_offers_enabled"]:
            return False, "User Offers are disabled in this server."
        if config and not config["user_offer_coin_transfers_enabled"]:
            return False, "User-offer coin transfers are disabled in this server."
        purchases = load_data("purchases")
        if confirmation_token:
            for purchase in purchases.values():
                if purchase.get("confirmation_token") == confirmation_token:
                    return True, purchase["purchase_id"]
        if not offer or offer.get("status") != "available" or offer.get("remaining_quantity", 0) <= 0:
            return False, "This offer is no longer available."
        if buyer_id == offer["seller_id"]:
            return False, "You cannot buy your own offer."
        minimum_level = max(
            config["minimum_purchase_level"],
            offer["minimum_buyer_level"]
        )
        if get_level(buyer_id) < minimum_level:
            return False, f"Requires Level {minimum_level}."
        if not can_afford(buyer_id, offer["price"]):
            return False, "You do not have enough coins."
        from modules.user_profile.profile_storage import (
            load_profiles,
            save_profiles
        )

        profiles_before = load_profiles()
        offers_before = deepcopy(offers)
        purchases_before = deepcopy(purchases)

        if not await transfer_coins(buyer_id, offer["seller_id"], offer["price"], offer_id):
            return False, "The purchase could not be completed."

        try:
            offer["remaining_quantity"] -= 1
            if offer["remaining_quantity"] == 0:
                offer["status"] = "completed"
            offer["updated_at"] = time.time()
            offers[offer_id] = offer
            save_data("offers", offers)
            purchase_id = str(uuid.uuid4())
            purchases[purchase_id] = {
                "purchase_id": purchase_id,
                "offer_id": offer_id,
                "type": "user_offer",
                "buyer_id": buyer_id,
                "seller_id": offer["seller_id"],
                "guild_id": offer["guild_id"],
                "price": offer["price"],
                "status": "reserved",
                "seller_completed": False,
                "buyer_received": False,
                "offer_name": offer["name"],
                "offer_description": offer["description"],
                "confirmation_token": confirmation_token,
                "created_at": time.time(),
                "updated_at": time.time()
            }
            save_data("purchases", purchases)
            return True, purchase_id
        except (OSError, TypeError, ValueError):
            save_data("offers", offers_before)
            save_data("purchases", purchases_before)
            save_profiles(profiles_before)
            return False, "The purchase could not be saved. No coins were charged."


def update_offer(seller_id, offer_id, **changes):
    offers = load_data("offers")
    offer = offers.get(offer_id)
    if not offer or offer.get("seller_id") != seller_id:
        return False, "Offer not found."

    if "price" in changes and int(changes["price"]) <= 0:
        return False, "Price must be greater than 0."
    if "quantity" in changes:
        quantity = int(changes["quantity"])
        sold = offer["quantity"] - offer["remaining_quantity"]
        if quantity < sold:
            return False, "Quantity cannot be below completed sales."
        offer["quantity"] = quantity
        offer["remaining_quantity"] = quantity - sold

    for key in ("name", "description", "price"):
        if key in changes:
            offer[key] = changes[key]
    offer["updated_at"] = time.time()
    offers[offer_id] = offer
    save_data("offers", offers)
    return True, offer


def set_offer_status(seller_id, offer_id, status):
    if status not in ("available", "disabled", "cancelled"):
        return False, "Invalid offer status."
    offers = load_data("offers")
    offer = offers.get(offer_id)
    if not offer or offer.get("seller_id") != seller_id:
        return False, "Offer not found."
    if offer.get("status") == "cancelled" and status != "cancelled":
        return False, "Cancelled offers cannot be re-enabled."
    offer["status"] = status
    offer["updated_at"] = time.time()
    offers[offer_id] = offer
    save_data("offers", offers)
    return True, offer


def transition_purchase(user_id, purchase_id, status):
    purchases = load_data("purchases")
    purchase = purchases.get(purchase_id)
    if not purchase:
        return False, "Purchase not found."
    if status == "received" and purchase.get("buyer_id") != user_id:
        return False, "Only the buyer can mark this received."
    if status == "completed" and purchase.get("seller_id") != user_id:
        return False, "Only the seller can mark this completed."
    if purchase.get("status") == "cancelled":
        return False, "Cancelled purchases cannot change status."
    if status == "received":
        if purchase.get("buyer_received"):
            return False, "Purchase already marked received."
        purchase["buyer_received"] = True
    elif status == "completed":
        if purchase.get("seller_completed"):
            return False, "Purchase already marked completed."
        purchase["seller_completed"] = True
    else:
        return False, "That purchase status change is not allowed."

    if purchase.get("seller_completed") and purchase.get("buyer_received"):
        purchase["status"] = "completed"
    else:
        purchase["status"] = "received" if purchase.get("buyer_received") else "reserved"
    purchase["updated_at"] = time.time()
    purchases[purchase_id] = purchase
    save_data("purchases", purchases)
    return True, purchase
