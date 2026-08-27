import discord

from modules.economy import get_coins, get_level
from .server_rewards import get_server_rewards


def marketplace_home(user):
    embed = discord.Embed(title="🏪 Marketplace")
    embed.description = (
        f"Level ✦ {get_level(user.id)}\n"
        f"Coins ✦ {get_coins(user.id)}"
    )
    return embed


def rewards_embed(user, page=0):
    rewards = get_server_rewards()
    start = page * 5
    embed = discord.Embed(title="Server Rewards")
    embed.description = f"Page {page + 1}"
    for reward in rewards[start:start + 5]:
        locked = get_level(user.id) < reward["required_level"]
        status = f"🔒 Requires Level {reward['required_level']}" if locked else f"{reward['price']} coins"
        embed.add_field(name=reward["name"], value=f"{status}\n{reward['description']}", inline=False)
    return embed


def offers_embed(offers, page=0):
    embed = discord.Embed(title="User Offers", description=f"Page {page + 1}")
    for offer in offers[page * 5:page * 5 + 5]:
        embed.add_field(name=offer["name"], value=f"{offer['price']} coins • {offer['remaining_quantity']} available\n{offer['description']}", inline=False)
    return embed
