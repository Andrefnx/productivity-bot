# Project Context

## Qué es

Bot de Discord escrito en Python con `discord.py`. Su producto activo gira alrededor de sesiones de escritura llamadas sprints: una persona crea un sprint, otras se unen, pueden elegir proyecto y registrar conteos de palabras, y el bot actualiza mensajes y resultados. También ofrece perfil, proyectos, configuración, ayuda e importación de datos de Writer Bot.

## Propósito actual

Facilitar sesiones de productividad/escritura dentro de Discord, conservar perfiles y proyectos en archivos JSON locales, y mostrar progreso personal mediante XP, niveles y monedas.

## Alcance demostrado

- Comandos públicos: `/sprint`, `/profile`, `/config`, `/help`.
- Sprints con espera, inicio, participantes, unión/salida, cambio de proyecto, conteo de palabras, resultados, recompensas y recuperación tras reinicio.
- Proyectos personales con creación, selección, edición, borrado, paginación, filtros/orden y conteo.
- Perfil con XP, nivel, monedas y último proyecto usado en sprints.
- Configuración de usuario, canal y sprint, permisos, privacidad y zona horaria.
- Ayuda navegable y apariencia del bot en servidores cuando el entitlement lo permite.
- Importación de perfiles/proyectos desde un JSON de Writer Bot.

## Dirección futura documentada

`notes/features.md` menciona capítulos, escenas, tareas, rachas, equipos, estadísticas, actividades adicionales, web y sincronización. Son roadmap/documentación, no requisitos actuales. `notes/systems.md` describe una fórmula de XP progresiva y multiplicadores que no coincide con la fórmula visible en `modules/economy.py`; la contradicción debe permanecer explícita.

## Conceptos principales

- **Sprint**: sesión temporizada con estado en memoria y un registro mínimo persistido para recuperación.
- **Participant / SprintUser**: estado de una persona dentro de un sprint.
- **Project**: diccionario persistido por usuario en `data/projects.json`.
- **Profile**: diccionario persistido por usuario en `data/profiles.json`.
- **XP / level / coins**: progresión global y saldo dentro del perfil.
- **View / Modal / callback**: componentes interactivos de `discord.py` que continúan los flujos después de una interacción.

## Límites de certeza

No se encontró configuración de despliegue ni una base de datos SQL. El proveedor de hosting, la configuración de producción y el historial de comandos antiguos fuera del script de limpieza son UNKNOWN.