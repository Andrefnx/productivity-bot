import discord
import uuid

from modules.economy import get_coins

from .market_embeds import marketplace_home, offers_embed, rewards_embed
from .purchases import purchase_server_reward
from .server_rewards import get_server_rewards
from .user_offers import (
    list_offers,
    purchase_offer,
    set_offer_status,
    update_offer
)
from .user_offers import create_offer
from .market_data import load_data
from .market_data import load_marketplace_config
from .market_permissions import can_sell
from .market_permissions import can_manage_marketplace
from .market_data import update_marketplace_config


# -------------------------------------------------------
#                  MARKETPLACE VIEW
# -------------------------------------------------------

class MarketplaceView(discord.ui.View):
    def __init__(self, owner):
        super().__init__(timeout=180)
        self.owner = owner
        self.page = 0
        self.mode = "home"
        self.build_home()

    def build_home(self):
        self.clear_items()
        self.add_item(self.server_rewards)
        self.add_item(self.user_offers)
        self.add_item(self.purchases)
        self.add_item(self.my_offers)
        if can_manage_marketplace(self.owner):
            self.add_item(self.marketplace_settings)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("This marketplace belongs to another user.", ephemeral=True)
            return False
        return True

    async def show(self, interaction):
        self.clear_items()
        if self.mode == "home":
            self.add_item(self.server_rewards)
            self.add_item(self.user_offers)
            self.add_item(self.purchases)
            self.add_item(self.my_offers)
            if can_manage_marketplace(self.owner):
                self.add_item(self.marketplace_settings)
        elif self.mode == "rewards":
            rewards = get_server_rewards()
            self.add_item(RewardSelect(self, rewards[self.page * 5:self.page * 5 + 5]))
            self.add_item(self.previous)
            self.add_item(self.next)
            self.add_item(self.back_home)
        elif self.mode == "offers":
            offers = list_offers(interaction.guild_id)
            self.add_item(OfferSelect(self, offers[self.page * 5:self.page * 5 + 5]))
            self.add_item(self.previous)
            self.add_item(self.next)
            self.add_item(self.back_home)
        elif self.mode == "purchases":
            purchases = [purchase for purchase in load_data("purchases").values() if purchase.get("buyer_id") == self.owner.id or purchase.get("seller_id") == self.owner.id]
            self.add_item(PurchaseSelect(self, purchases))
            self.add_item(self.mark_received)
            self.add_item(self.mark_completed)
            self.add_item(self.back_home)
        elif self.mode == "my_offers":
            offers = [offer for offer in load_data("offers").values() if offer.get("seller_id") == self.owner.id]
            self.add_item(OfferManagementSelect(self, offers))
            self.add_item(self.create_offer_button)
            self.add_item(self.edit_offer_button)
            self.add_item(self.disable_offer_button)
            self.add_item(self.enable_offer_button)
            self.add_item(self.cancel_offer_button)
            self.add_item(self.back_home)
        elif self.mode == "admin":
            self.add_item(AdminSettingSelect(self))
            self.add_item(AdminValueSelect(self, interaction.guild_id))
            self.add_item(self.save_admin_setting)
            self.add_item(self.back_home)
        await interaction.response.edit_message(embed=self.embed(interaction), view=self)

    def embed(self, interaction):
        if self.mode == "home":
            return marketplace_home(self.owner)
        if self.mode == "rewards":
            return rewards_embed(self.owner, self.page)
        if self.mode == "purchases":
            embed = discord.Embed(title="Purchases")
            purchases = load_data("purchases")
            own = [purchase for purchase in purchases.values() if purchase.get("buyer_id") == self.owner.id or purchase.get("seller_id") == self.owner.id]
            for purchase in own[-10:]:
                embed.add_field(name=purchase.get("offer_id", purchase.get("reward_id", "Purchase")), value=f"{purchase.get('price', 0)} coins • {purchase.get('status', 'completed')}", inline=False)
            return embed
        if self.mode == "my_offers":
            offers = [offer for offer in load_data("offers").values() if offer.get("seller_id") == self.owner.id]
            return offers_embed(offers, 0)
        if self.mode == "admin":
            config = load_marketplace_config(interaction.guild_id)
            return discord.Embed(
                title="Marketplace Settings",
                description="Configure basic marketplace access.\n\n"
                + "\n".join(f"{key}: `{value}`" for key, value in config.items())
            )
        return offers_embed(list_offers(interaction.guild_id), self.page)

    @discord.ui.button(label="Server Rewards", style=discord.ButtonStyle.primary, row=0)
    async def server_rewards(self, interaction, button):
        self.mode = "rewards"
        self.page = 0
        await self.show(interaction)

    @discord.ui.button(label="User Offers", style=discord.ButtonStyle.secondary, row=0)
    async def user_offers(self, interaction, button):
        if not load_marketplace_config(interaction.guild_id)["user_offers_enabled"]:
            await interaction.response.send_message("User Offers are disabled in this server.", ephemeral=True)
            return
        self.mode = "offers"
        self.page = 0
        await self.show(interaction)

    @discord.ui.button(label="Purchases", style=discord.ButtonStyle.secondary, row=0)
    async def purchases(self, interaction, button):
        self.mode = "purchases"
        await self.show(interaction)

    @discord.ui.button(label="Mark Received", style=discord.ButtonStyle.secondary, row=3)
    async def mark_received(self, interaction, button):
        await self.update_purchase(interaction, "received")

    @discord.ui.button(label="Mark Completed", style=discord.ButtonStyle.secondary, row=4)
    async def mark_completed(self, interaction, button):
        await self.update_purchase(interaction, "completed")

    async def update_purchase(self, interaction, status):
        purchase_id = getattr(self, "selected_purchase_id", None)
        if not purchase_id:
            await interaction.response.send_message("Select a purchase first.", ephemeral=True)
            return
        success, result = transition_purchase(
            self.owner.id,
            purchase_id,
            status
        )
        if not success:
            await interaction.response.send_message(result, ephemeral=True)
            return
        await self.show(interaction)

    @discord.ui.button(label="My Offers", style=discord.ButtonStyle.secondary, row=0)
    async def my_offers(self, interaction, button):
        config = load_marketplace_config(interaction.guild_id)
        if not config["user_offers_enabled"]:
            await interaction.response.send_message("User Offers are disabled in this server.", ephemeral=True)
            return
        if not can_sell(self.owner.id, interaction.guild_id):
            await interaction.response.send_message("User Offers unlock at Level 10.", ephemeral=True)
            return
        self.mode = "my_offers"
        await self.show(interaction)

    @discord.ui.button(label="Create Offer", style=discord.ButtonStyle.primary, row=1)
    async def create_offer_button(self, interaction, button):
        await interaction.response.send_modal(CreateOfferModal(self.owner.id, interaction.guild_id))

    @discord.ui.button(label="Marketplace Settings", style=discord.ButtonStyle.secondary, row=2)
    async def marketplace_settings(self, interaction, button):
        if not can_manage_marketplace(interaction.user):
            await interaction.response.send_message("Administrator or Manage Server permission required.", ephemeral=True)
            return
        self.mode = "admin"
        self.page = 0
        self.admin_key = "marketplace_enabled"
        await self.show(interaction)

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.secondary, row=2)
    async def edit_offer_button(self, interaction, button):
        offer = self.selected_offer()
        if offer is None:
            await interaction.response.send_message("Select an offer first.", ephemeral=True)
            return
        await interaction.response.send_modal(EditOfferModal(self.owner.id, offer))

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.secondary, row=2)
    async def disable_offer_button(self, interaction, button):
        await self.change_offer_status(interaction, "disabled")

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.secondary, row=2)
    async def enable_offer_button(self, interaction, button):
        await self.change_offer_status(interaction, "available")

    @discord.ui.button(label="Cancel Offer", style=discord.ButtonStyle.danger, row=3)
    async def cancel_offer_button(self, interaction, button):
        await self.change_offer_status(interaction, "cancelled")

    def selected_offer(self):
        offer_id = getattr(self, "selected_offer_id", None)
        if not offer_id:
            return None
        return load_data("offers").get(offer_id)

    async def change_offer_status(self, interaction, status):
        offer = self.selected_offer()
        if offer is None:
            await interaction.response.send_message("Select an offer first.", ephemeral=True)
            return
        success, result = set_offer_status(self.owner.id, offer["offer_id"], status)
        if not success:
            await interaction.response.send_message(result, ephemeral=True)
            return
        await self.show(interaction)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=1)
    async def previous(self, interaction, button):
        self.page = max(0, self.page - 1)
        await self.show(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=1)
    async def next(self, interaction, button):
        max_page = 0
        if self.mode == "rewards":
            max_page = max(0, (len(get_server_rewards()) - 1) // 5)
        elif self.mode == "offers":
            max_page = max(0, (len(list_offers(interaction.guild_id)) - 1) // 5)
        self.page = min(max_page, self.page + 1)
        await self.show(interaction)

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_home(self, interaction, button):
        self.mode = "home"
        self.page = 0
        await self.show(interaction)

    @discord.ui.button(label="Save Setting", style=discord.ButtonStyle.success, row=3)
    async def save_admin_setting(self, interaction, button):
        if not can_manage_marketplace(interaction.user):
            await interaction.response.send_message("Administrator or Manage Server permission required.", ephemeral=True)
            return
        config = load_marketplace_config(interaction.guild_id)
        key = getattr(self, "admin_key", "marketplace_enabled")
        value = getattr(self, "admin_value", str(config[key]))
        if key in ("marketplace_enabled", "user_offers_enabled", "user_offer_coin_transfers_enabled"):
            value = value == "true"
        else:
            value = int(value)
        update_marketplace_config(interaction.guild_id, key, value)
        await self.show(interaction)


class AdminSettingSelect(discord.ui.Select):
    def __init__(self, view):
        self.market_view = view
        keys = (
            "marketplace_enabled",
            "minimum_purchase_level",
            "minimum_seller_level",
            "user_offers_enabled",
            "user_offer_coin_transfers_enabled"
        )
        super().__init__(
            placeholder="Select marketplace setting",
            options=[
                discord.SelectOption(
                    label=key.replace("_", " ").title(),
                    value=key,
                    default=(key == getattr(view, "admin_key", keys[0]))
                )
                for key in keys
            ],
            row=0
        )

    async def callback(self, interaction):
        self.market_view.admin_key = self.values[0]
        self.market_view.admin_value = None
        await self.market_view.show(interaction)


class AdminValueSelect(discord.ui.Select):
    def __init__(self, view, guild_id):
        self.market_view = view
        config = load_marketplace_config(guild_id)
        key = getattr(view, "admin_key", "marketplace_enabled")
        if key in ("marketplace_enabled", "user_offers_enabled", "user_offer_coin_transfers_enabled"):
            values = (("Enabled", "true"), ("Disabled", "false"))
        elif key == "minimum_purchase_level":
            values = tuple((f"Level {value}", str(value)) for value in range(3, 21))
        else:
            values = tuple((f"Level {value}", str(value)) for value in range(10, 21))
        current = str(config[key]).lower()
        super().__init__(
            placeholder="Select setting value",
            options=[discord.SelectOption(label=label, value=value, default=value == current) for label, value in values],
            row=1
        )

    async def callback(self, interaction):
        self.market_view.admin_value = self.values[0]
        await self.market_view.show(interaction)


class RewardSelect(discord.ui.Select):
    def __init__(self, view, rewards):
        self.market_view = view
        super().__init__(placeholder="Select a reward", options=[discord.SelectOption(label=r["name"], value=r["reward_id"]) for r in rewards], row=0)

    async def callback(self, interaction):
        reward_id = self.values[0]
        token = str(uuid.uuid4())
        view = RewardConfirmationView(
            interaction.user.id,
            reward_id,
            interaction.guild_id,
            token
        )
        await interaction.response.send_message(
            "Confirm this reward purchase?",
            view=view,
            ephemeral=True
        )


class RewardConfirmationView(discord.ui.View):
    def __init__(self, buyer_id, reward_id, guild_id, token):
        super().__init__(timeout=60)
        self.buyer_id = buyer_id
        self.reward_id = reward_id
        self.guild_id = guild_id
        self.token = token

    async def interaction_check(self, interaction):
        return interaction.user.id == self.buyer_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        success, result = await purchase_server_reward(
            self.buyer_id,
            self.reward_id,
            self.guild_id,
            self.token
        )
        await interaction.response.edit_message(
            content=result if not success else "Purchase completed.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Purchase cancelled.",
            view=None
        )
        self.stop()


class OfferSelect(discord.ui.Select):
    def __init__(self, view, offers):
        self.market_view = view
        options = [discord.SelectOption(label=offer["name"][:100], value=offer["offer_id"], description=f"{offer['price']} coins") for offer in offers]
        if not options:
            options = [discord.SelectOption(label="No offers available", value="none")]
        super().__init__(placeholder="Select a user offer", options=options, disabled=not offers, row=0)

    async def callback(self, interaction):
        offer = next((offer for offer in list_offers(interaction.guild_id) if offer["offer_id"] == self.values[0]), None)
        if offer is None:
            await interaction.response.send_message("This offer is no longer available.", ephemeral=True)
            return
        token = str(uuid.uuid4())
        view = OfferConfirmationView(
            interaction.user.id,
            offer,
            token
        )
        await interaction.response.send_message(
            f'Buy "{offer["name"]}" for {offer["price"]} coins?\n\n'
            f'Your balance: {get_coins(interaction.user.id)} → '
            f'{get_coins(interaction.user.id) - offer["price"]} coins',
            view=view,
            ephemeral=True
        )


class OfferConfirmationView(discord.ui.View):
    def __init__(self, buyer_id, offer, token):
        super().__init__(timeout=60)
        self.buyer_id = buyer_id
        self.offer = offer
        self.token = token

    async def interaction_check(self, interaction):
        return interaction.user.id == self.buyer_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        success, result = await purchase_offer(
            self.buyer_id,
            self.offer["offer_id"],
            self.token
        )
        await interaction.response.edit_message(
            content=result if not success else "Offer purchased.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Purchase cancelled.",
            view=None
        )
        self.stop()


class OfferManagementSelect(discord.ui.Select):
    def __init__(self, view, offers):
        self.market_view = view
        options = [
            discord.SelectOption(
                label=offer["name"][:100],
                value=offer["offer_id"],
                description=offer.get("status", "available")
            )
            for offer in offers
        ]
        if not options:
            options = [
                discord.SelectOption(
                    label="No offers created",
                    value="none"
                )
            ]
        super().__init__(
            placeholder="Select your offer",
            options=options,
            disabled=not offers,
            row=0
        )

    async def callback(self, interaction):
        self.market_view.selected_offer_id = self.values[0]
        await self.market_view.show(interaction)


class PurchaseSelect(discord.ui.Select):
    def __init__(self, view, purchases):
        self.market_view = view
        options = [
            discord.SelectOption(
                label=purchase.get("offer_name", purchase.get("reward_id", "Purchase"))[:100],
                value=purchase["purchase_id"],
                description=purchase.get("status", "completed")
            )
            for purchase in purchases[-25:]
        ]
        if not options:
            options = [discord.SelectOption(label="No purchases", value="none")]
        super().__init__(
            placeholder="Select a purchase or sale",
            options=options,
            disabled=not purchases,
            row=0
        )

    async def callback(self, interaction):
        self.market_view.selected_purchase_id = self.values[0]
        await self.market_view.show(interaction)


class CreateOfferModal(discord.ui.Modal):
    def __init__(self, seller_id, guild_id):
        super().__init__(title="Create Offer")
        self.seller_id = seller_id
        self.guild_id = guild_id
        self.name_input = discord.ui.TextInput(label="Offer name", max_length=100)
        self.description_input = discord.ui.TextInput(label="Description", max_length=500)
        self.price_input = discord.ui.TextInput(label="Price", max_length=8)
        self.level_input = discord.ui.TextInput(label="Minimum buyer level", default="3", max_length=3)
        self.quantity_input = discord.ui.TextInput(label="Quantity", default="1", max_length=6)
        for field in (self.name_input, self.description_input, self.price_input, self.level_input, self.quantity_input):
            self.add_item(field)

    async def on_submit(self, interaction):
        try:
            price = int(self.price_input.value)
            level = int(self.level_input.value)
            quantity = int(self.quantity_input.value)
        except ValueError:
            await interaction.response.send_message("Price, level, and quantity must be numbers.", ephemeral=True)
            return

        offer = create_offer(
            self.seller_id,
            self.guild_id,
            self.name_input.value,
            self.description_input.value,
            price,
            level,
            quantity
        )
        if offer is None:
            await interaction.response.send_message("Offers require Level 10 and valid values.", ephemeral=True)
            return

        await interaction.response.send_message("Offer created.", ephemeral=True)


class EditOfferModal(discord.ui.Modal):
    def __init__(self, seller_id, offer):
        super().__init__(title="Edit Offer")
        self.seller_id = seller_id
        self.offer = offer
        self.name_input = discord.ui.TextInput(
            label="Offer name",
            default=offer["name"],
            max_length=100
        )
        self.description_input = discord.ui.TextInput(
            label="Description",
            default=offer["description"],
            max_length=500
        )
        self.price_input = discord.ui.TextInput(
            label="Price",
            default=str(offer["price"]),
            max_length=8
        )
        self.quantity_input = discord.ui.TextInput(
            label="Quantity",
            default=str(offer["quantity"]),
            max_length=6
        )
        for field in (
            self.name_input,
            self.description_input,
            self.price_input,
            self.quantity_input
        ):
            self.add_item(field)

    async def on_submit(self, interaction):
        try:
            price = int(self.price_input.value)
            quantity = int(self.quantity_input.value)
        except ValueError:
            await interaction.response.send_message(
                "Price and quantity must be numbers.",
                ephemeral=True
            )
            return

        success, result = update_offer(
            self.seller_id,
            self.offer["offer_id"],
            name=self.name_input.value,
            description=self.description_input.value,
            price=price,
            quantity=quantity
        )
        await interaction.response.send_message(
            "Offer updated." if success else result,
            ephemeral=True
        )
