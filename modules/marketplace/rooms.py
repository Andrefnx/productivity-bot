import time
import uuid

from .market_data import load_data, save_data


def record_room(guild_id, channel_id, owner_id, expires_at, invited_user_ids=None):
    data = load_data("rooms")
    room_id = str(uuid.uuid4())
    data[room_id] = {
        "room_id": room_id,
        "guild_id": guild_id,
        "channel_id": channel_id,
        "owner_id": owner_id,
        "created_at": time.time(),
        "expires_at": expires_at,
        "invited_user_ids": invited_user_ids or [],
        "status": "active"
    }
    save_data("rooms", data)
    return data[room_id]


def remove_room(room_id):
    data = load_data("rooms")
    if room_id in data:
        data[room_id]["status"] = "deleted"
        save_data("rooms", data)
        return True
    return False
