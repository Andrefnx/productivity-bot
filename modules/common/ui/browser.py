import discord


def create_browser_state_embed(
    sort_label,
    filter_label,
    page,
    total_pages
):
    return discord.Embed(
        description=(
            f"**{sort_label}** ✦ **{filter_label}** ✦ "
            f"**Page {page + 1}/{total_pages}**"
        )
    )