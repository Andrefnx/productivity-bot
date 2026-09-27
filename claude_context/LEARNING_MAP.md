# Learning Map

## FOUNDATIONAL FOR CURRENT CODE

**Variables, parameters and return values**  
Used in every module, especially `modules/sprints/users.py` and `modules/user_profile/projects/project_list.py`. Study how dictionaries and IDs travel between functions.

**Functions, modules and imports**  
`main.py` imports public surfaces from package `__init__.py` files; trace `modules/sprints/__init__.py` and `modules/user_profile/__init__.py`.

**Classes, objects, `__init__`, attributes**  
`SprintUser`, `SprintParticipants`, `ProfileView`, project Views and Modals store state on `self`.

**Collections**  
Participant dictionaries, project dictionaries, lists of users/results, and JSON-shaped nested dictionaries are central to state.

## CURRENTLY USEFUL

**async/await and coroutines**  
Used by command functions, `on_ready`, View callbacks, Modal `on_submit`, timers and Discord API calls. Examples: `main.sprint()`, `main.on_ready()`, `sprint_results.close_results_registration()`.

**Callbacks and event-driven programming**  
Discord invokes `@tree.command`, `@client.event`, button methods, Select callbacks and Modal `on_submit`; the user does not call these like ordinary synchronous functions.

**Inheritance and decorators**  
`class ProfileView(discord.ui.View)` and `class WriterBotImportModal(discord.ui.Modal)` inherit framework behavior. `@discord.ui.button` and `@tree.command` register callbacks.

**State management and persistence**  
Runtime state is held in sprint objects; durable state is read/written by `profile_storage.py`, `project_list.py`, config modules and `system_messages.py` using JSON.

**Exceptions and API boundaries**  
`discord.Forbidden`, `discord.HTTPException`, `discord.NotFound`, JSON errors and validation failures are handled in several paths.

**Type hints**  
Selected functions use annotations such as `user_id: int`; many functions intentionally rely on inferred/dynamic types. Compare annotations with actual Discord objects.

## NEXT CONCEPTS

**APIs and framework objects**  
Learn `discord.Interaction`, `discord.Embed`, `discord.Client`, `CommandTree`, `View`, `Modal`, `Button` and `Select` by tracing one sprint interaction.

**Concurrency and task lifecycle**  
Study `asyncio.create_task`, `asyncio.sleep`, cancellation, locks and timers in sprint/reward flows.

**Data modeling**  
Compare plain dict records in JSON with Python objects such as `SprintUser`; identify where invariants are enforced.

## LATER / ADVANCED

**Transactions and idempotency**  
`award_sprint_result()` uses a reward key to avoid awarding twice; `economy.py` also has an async lock for transfers. This is a good bridge to atomicity and failure recovery.

**Architecture boundaries**  
Explore how UI, domain state, persistence and Discord messaging are coupled before considering refactoring.

## Explicit contradiction to study

`notes/systems.md` documents progressive level XP and complexity multipliers, while `modules/economy.py` currently calculates level as `xp // 100 + 1` and uses fixed duration/word formulas. Read both and ask which is current implementation versus design intent.