# Architecture

## Stack and startup

- Python; versión mínima de Python: UNKNOWN. `requirements.txt` pide `discord.py>=2.7`, `aiohttp>=3.8`, `python-dotenv==1.2.3` y `tzdata>=2025.1`.
- Entry point: `main.py`.
- `load_dotenv()` carga `.env`; `DISCORD_TOKEN` es obligatorio. `BOT_OWNER_ID` y `PREMIUM_GUILD_IDS` aparecen en el entorno, pero su uso debe seguirse en `modules/common/entitlements.py`.
- `discord.Intents.default()`, `discord.Client`, `app_commands.CommandTree`.
- El bloque `if __name__ == "__main__"` crea archivos runtime y llama `client.run(token)`.
- `on_ready()` recupera sprints una sola vez mediante `recover_interrupted_sprints(client)`, luego ejecuta `tree.sync()`.

## Command tree

`main.py` registra cuatro slash commands globales:

- `/sprint`: lee configuración de canal y permiso; abre `SprintCreateModal`.
- `/profile`: difiere la respuesta y envía embed de perfil con `ProfileView`.
- `/config`: envía `ConfigMenuView` de forma efímera.
- `/help`: envía `HelpView` y el embed de ayuda.

No hay evidencia de que `/market` o `/ping` estén registrados actualmente. `scripts/cleanup_legacy_guild_commands.py` puede eliminarlos de un guild.

## Flujo real de `/sprint`

`/sprint` -> `sprint()` en `main.py` -> `get_channel_config()` y `can_create_sprint()` -> `SprintCreateModal` -> submit del modal en `modules/sprints/active_sprint.py` -> creación de `SprintView`/estado de sprint -> embed de espera y registro en `data/active_sprints.json` -> `asyncio` espera el inicio -> `start_sprint()` edita el mensaje y comienza el timer -> participantes interactúan con `JoinSprintView` -> `ProjectPickerView` y selección de conteo inicial -> `SprintUser` en `SprintParticipants` -> actividad/proyecto y `sprint_activity.py` -> modal compartido de conteo -> actualización de proyecto/perfil -> finalización -> registro de resultados -> `award_sprint_result()` -> embed final.

El nombre exacto de la clase principal del sprint y los métodos intermedios deben verificarse en el archivo antes de editar; el flujo se reparte entre `active_sprint.py`, `users.py`, `sprint_activity.py`, `sprint_results.py` y `system_messages.py`.

## UI y callbacks

`discord.ui.View` contiene botones/selects y puede tener `interaction_check()`. Los decoradores `@discord.ui.button` convierten métodos en callbacks gestionados por `discord.py`. `discord.ui.Select.callback()` puede delegar a un método de su View. `discord.ui.Modal.on_submit()` recibe la interacción después del envío del modal. El callback usa `interaction.response` una vez para responder, y `followup` cuando la interacción ya fue respondida o diferida.

Views suelen guardar `owner`/`owner_id`, aplicar autorización en `interaction_check`, editar el mensaje y construir otra View. Los datos de negocio no viven en Discord: se cargan desde JSON y algunos estados temporales viven en objetos Python.

## Estado y persistencia

- `data/active_sprints.json`: registro de guild/channel/message de sprints activos para recuperación.
- `data/sprint_users.json`: almacenamiento relacionado con usuarios de sprint; el uso debe seguirse antes de modificarlo.
- `data/profiles.json`: perfiles, XP, nivel, último proyecto, palabras fuera de proyectos y economía.
- `data/projects.json`: proyectos por `user_id` y `project_id`.
- `data/channel_config.json`: configuración por canal.
- `modules/common/runtime_data.py`: crea archivos ausentes con defaults.
- El almacenamiento es JSON síncrono mediante `json.load/json.dump`; no existe SQL ni ORM demostrado.

## Configuración y permisos

`modules/config/` separa configuración de usuario, canal y sprint; `permissions.py` resuelve administrador, moderador, creador y settings efectivos. `visibility.py` decide exposición de perfil/proyectos. La configuración se aplica desde callbacks y se refleja en embeds/views.

## Recovery y timers

`system_messages.py` carga el registro activo y recupera mensajes; maneja errores de Discord durante recuperación. `active_sprint.py` usa tareas asíncronas para espera, actividad y timeout de sprint vacío. `sprint_results.py` espera la ventana de registro y envía recordatorios. Los timers son runtime y no son serializados como tareas; al reiniciar se reconstruyen desde el registro y mensajes disponibles.

Al cerrar resultados, el ranking usa participantes con WC registrado; quienes
participaron sin conteo de palabras se muestran aparte, sin puesto numérico.

## Deployment

No hay Dockerfile, Procfile, workflow, manifiesto de proveedor ni documentación de hosting detectada. El proceso conocido es ejecutar `python main.py` con un `.env` que contenga `DISCORD_TOKEN`.