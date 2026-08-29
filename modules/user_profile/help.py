PROFILE_TITLE = "Profile"

PROFILE_DESCRIPTION = (
    "Use `/profile` to open your personal bot menu.\n\n"
    "Your profile currently shows:\n"
    "• Your name\n"
    "• EXP information\n"
    "• Your last project used in a sprint\n\n"
    "From your profile you can open:\n"
    "• My Projects\n"
    "• Import JSON\n"
    "• Settings\n\n"
    "Your own profile menu is private to you.\n\n"
    "Your privacy settings control whether other users will be "
    "allowed to view your profile or projects when public profile "
    "viewing is used."
)


def register_help(registry):
    registry.register(
        key="profile",
        label="Profile",
        description="Your personal bot menu",
        order=30,
        renderer=lambda: (PROFILE_TITLE, PROFILE_DESCRIPTION)
    )
