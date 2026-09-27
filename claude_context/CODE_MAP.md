# Code Map

## Recommended reading order

1. `README.md` and `requirements.txt`: minimal project description and runtime packages.
2. `main.py`: imports, token loading, client/tree creation, four commands and `on_ready`.
3. `modules/common/runtime_data.py`: why runtime JSON files exist.
4. `modules/sprints/active_sprint.py`: command-to-sprint orchestration.
5. `modules/sprints/users.py`: `SprintUser`, `SprintParticipants`, join and project/count flow.
6. `modules/sprints/system_messages.py`: embeds, active-sprint registry and recovery.
7. `modules/sprints/sprint_activity.py` and `sprint_results.py`: activity changes, word count and closeout.
8. `modules/user_profile/profile_storage.py` then `profile.py`: profile state and profile UI.
9. `modules/user_profile/projects/project_list.py`, `project_views.py`, `project_modals.py`: project record and browser.
10. `modules/economy.py`: XP, levels, coins and reward formulas.
11. `modules/config/`: settings resolution, permissions, visibility and timezone.
12. `modules/help/` and `modules/bot_appearance/`: smaller View/registry patterns.
13. `modules/user_profile/imports/`: JSON parsing and mapping boundary.
14. `modules/marketplace/`: read only after confirming its active caller; current public reachability is UNKNOWN.
15. `tests/`: executable examples and assumptions, especially entry points and sprint lifecycle.

## Important modules

### `main.py`
- Purpose: process entry point and Discord wiring.
- Important symbols: `client`, `tree`, `sprint`, `profile`, `config`, `help_command`, `on_ready`.
- Imports/dependencies: `discord`, dotenv, sprint/profile/config/help package exports.
- Who calls it: Python process; Discord dispatches registered commands/events.
- State read: `.env`, channel config, Discord interaction.
- State modified: command registration and remote Discord messages; startup recovery flag.
- Related: all public package surfaces.

### `modules/sprints/active_sprint.py`
- Purpose: create and run sprint UI/lifecycle.
- Important classes/functions: `SprintCreateModal`, `ConfirmationView`, `SprintSettingsMenuView`, `SprintTimeView`, sprint lifecycle methods on the active sprint object, notification helpers.
- Imports: config permissions/settings, project picker, messages, activity, system messages, users.
- Called by: `/sprint` and callbacks from sprint UI.
- Reads: channel config, sprint config, participants, Discord message state.
- Modifies: sprint runtime object, Discord embeds/views, active sprint registry, participant/project state.
- Related: `users.py`, `system_messages.py`, `sprint_activity.py`, `sprint_results.py`.

### `modules/sprints/users.py`
- Purpose: participant domain state and joining/project selection.
- Important classes: `SprintUser`, `SprintParticipants`, `JoinSprintView`, word-count selection views.
- Reads: user/project/profile data and sprint settings.
- Modifies: participant dictionary, activity history, last project, project wordcount.
- Called by: active sprint callbacks and activity flow.

### `modules/sprints/system_messages.py`
- Purpose: sprint embeds and persisted active-sprint registry/recovery.
- Important functions: `load_active_sprints`, `save_active_sprints`, `register_active_sprint`, `remove_active_sprint`, `recover_interrupted_sprints`, embed builders and status updates.
- Reads/writes: `data/active_sprints.json`; Discord guild/channel/message APIs.
- Called by: startup and lifecycle transitions.

### `modules/sprints/sprint_activity.py` / `sprint_results.py`
- Purpose: mid-sprint activity/project/count changes and post-sprint registration.
- Important symbols: `ActivityChangeView`, `ActivityProjectView`, result registration helpers, reminder/close tasks.
- State read: participants, project records, timers.
- State modified: `SprintUser`, project wordcount, final result embeds and reward state.

### `modules/user_profile/profile_storage.py`
- Purpose: JSON profile repository.
- Important functions: `load_profiles`, `save_profiles`, `get_profile`, `update_profile`, `set_last_project`, `add_words_outside_projects`.
- State: `data/profiles.json`; creates defaults and merges economy defaults.
- Called by: profile UI, economy, project/sprint flows and imports.

### `modules/user_profile/profile.py`
- Purpose: profile embed and profile View.
- Important symbols: `get_last_project`, `create_profile_embed`, `ProfileView`.
- Called by `/profile` and profile buttons.
- Reads: profile/project/config visibility.
- Modifies: message navigation; import/project/settings flows.

### `modules/user_profile/projects/project_list.py`
- Purpose: project JSON repository and domain operations.
- Important functions: `load_projects`, `save_projects`, `get_user_projects`, `get_project`, `create_project`, `update_project`, deletion and word-count helpers.
- State: `data/projects.json` keyed by string user ID then project ID.
- Called by project Views, sprint users and Writer Bot import.

### `modules/user_profile/projects/project_views.py` / `project_modals.py`
- Purpose: paginated project browser, picker, detail/edit/delete UI and forms.
- Important classes: `UserProjectsView`, `ProjectPickerView`, `ProjectDetailView`, `CreateProjectView`, project confirmation/modal classes.
- Reads: project list, user config and profile.
- Modifies: project records and Discord message navigation.

### `modules/economy.py`
- Purpose: XP/level/coin calculations, wallet operations and sprint rewards.
- Important functions: `calculate_level`, `get_xp_progress`, `get_coins`, `spend_coins`, `credit_coins`, `transfer_coins`, `award_xp`, `award_sprint_result`.
- Reads/writes: nested `economy` in `profiles.json` via profile storage.
- Called by profile display, sprint reward closeout and marketplace code.

### `modules/config/`
- Purpose: settings and policy boundary.
- Important modules: `user_config.py`, `channel_config.py`, `sprint_config.py`, `permissions.py`, `visibility.py`, `timezone.py`, `config_menu.py`, `*_views.py`.
- State: user/channel JSON configuration and Discord permission objects.
- Called by main commands and nearly every protected View.

### `modules/marketplace/`
- Purpose: marketplace config, rewards, purchases and user offers.
- Important symbols: `MarketplaceView`, `create_offer`, `list_offers`, `purchase_offer`, `purchase_server_reward`.
- State/dependencies: profiles/economy and marketplace data modules.
- Caller: current active caller and public command reachability UNKNOWN; do not assume it is user-accessible.

### `modules/user_profile/imports/`
- Purpose: accept Writer Bot JSON, validate/parse it, map projects/statuses and merge into local profile/projects.
- Important symbols: `ImportSourceView`, `WriterBotImportModal`, `convert_writer_bot_project`, `import_writer_bot_projects`, `import_writer_bot_profile`.
- State modified: `profiles.json` and `projects.json`; raw source data is retained in mapped project fields.

### `tests/`
- Purpose: executable contracts for entry points, sprint lifecycle, UI layout, project behavior, entitlements and timezone privacy.
- Who calls code: unittest test cases, often with mocks/fakes.
- Read first: `test_entry_points.py`, `test_sprint_join.py`, `test_sprint_lifecycle_recovery.py`, `test_project_browser.py`, `test_timezone_privacy.py`.

### `scripts/cleanup_legacy_guild_commands.py`
- Purpose: optional maintenance script for guild-specific obsolete commands.
- Important functions: `parse_arguments`, `remove_legacy_commands`, `main`.
- Reads: `.env`, guild command API.
- Modifies: remote guild command registrations; requires explicit operational authorization.