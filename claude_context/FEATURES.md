# Features Inventory

## IMPLEMENTED

- **Discord startup and four public commands**: `main.py`.
- **Sprint lifecycle**: `modules/sprints/active_sprint.py`, `users.py`, `sprint_activity.py`, `sprint_results.py`, `system_messages.py`.
- **Join/leave and participant state**: `modules/sprints/users.py`.
- **Project CRUD, browser and selection**: `modules/user_profile/projects/project_list.py`, `project_views.py`, `project_modals.py`.
- **Word count tracking**: `modules/common/validation.py`, `modules/common/ui/modals.py`, sprint activity/results and project list.
- **Profiles and last project**: `modules/user_profile/profile.py`, `profile_storage.py`.
- **XP/levels/coins and sprint rewards**: `modules/economy.py` and profile economy data.
- **User/channel/sprint settings, permissions, privacy, timezone**: `modules/config/`.
- **Help navigation**: `modules/help/`.
- **Bot appearance settings**: `modules/bot_appearance/`.
- **Writer Bot JSON import**: `modules/user_profile/imports/`.
- **Runtime file initialization and sprint recovery**: `modules/common/runtime_data.py`, `modules/sprints/system_messages.py`.

## PARTIALLY IMPLEMENTED / INTEGRATION UNKNOWN

- **Marketplace**: substantial code exists in `modules/marketplace/` for rewards, offers, rooms, purchases and views; no current public command or import from `main.py` proves that users can reach it. Treat as code present with active reachability UNKNOWN until traced from a current View.
- **Bot customization entitlement**: implementation exists, availability depends on `modules/common/entitlements.py` and server configuration.
- **Non-writing activities**: no-word-count mode exists in sprint participant logic; broader V2 “different activity types” remains documented future work.
- **Recovery**: active sprint registry and message recovery exist, but external Discord permissions/errors can prevent full recovery.

## CURRENTLY IN DEVELOPMENT / EVIDENCE OF TRANSITION

- Legacy setting aliases and legacy sprint join paths remain in code (`LEGACY_*`, `finish_legacy_join`, cleanup script). This indicates compatibility or migration code, not a new product requirement.
- The repository's latest commit implements active sprint status updates and recovery logic.

## PLANNED / DOCUMENTED

`notes/features.md`: chapters, scenes, tasks/subtasks, streaks, teams, richer statistics, expanded economy/marketplace, writing website and synchronization. These are not confirmed implemented features.

## EXPERIMENTAL / IDEA

No separate experimental marker was found. Any TODO-like or speculative text must be treated as UNKNOWN until connected to executable code.

## OBSOLETE / SUPERSEDED

The cleanup script identifies guild commands `market` and `ping` as obsolete candidates. It does not prove how or when they became obsolete. Legacy aliases/migration fields are compatibility paths.

## UNKNOWN

Hosting provider, production deployment, SQL database, command registration outside `main.py`, and whether all marketplace Views are reachable from an active interaction path.