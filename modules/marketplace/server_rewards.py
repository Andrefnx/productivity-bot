from .rewards import SERVER_REWARDS


def get_server_rewards():
    return [reward.copy() for reward in SERVER_REWARDS]


def get_server_reward(reward_id):
    return next((reward.copy() for reward in SERVER_REWARDS if reward["reward_id"] == reward_id), None)
