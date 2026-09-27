# Tools Recommendations

## REQUIRED

- **Filesystem/repository read access**: resolvería leer `main.py`, módulos, tests, `notes/` y `data` sin depender de resúmenes. Debe ser read-only por defecto; riesgo: exposición de runtime data y secretos.
- **Python runtime**: necesario para ejecutar imports y checks locales. Permiso de ejecución en un entorno aislado; no necesita acceso de escritura fuera del workspace.
- **Test runner/terminal**: necesario para `unittest` y comandos de diagnóstico. Read/write solo dentro de un workspace temporal cuando un test lo requiera; nunca acceso operativo a producción por defecto.

## HIGH VALUE

- **Git read-only**: historial, diff, branch y blame ayudan a distinguir intención de regresión. No autorizar commit/push sin petición separada.
- **Documentación oficial de discord.py**: útil para `Interaction`, `CommandTree`, Views, Modals, limits y excepciones. Acceso web read-only.
- **Discord API test server**: útil para probar permisos, callbacks y recuperación, pero requiere credenciales y efectos remotos. Solo con autorización explícita, guild de prueba y secretos introducidos por el usuario fuera del contexto.

## OPTIONAL

- **JSON inspection tool**: útil para inspeccionar esquemas de `data/*.json` sin imprimir valores de usuarios. Read-only y con redacción.
- **Browser/web access**: útil para documentación de Python/discord.py y eventualmente comprobar enlaces; no es necesario para entender el código local.
- **Static analysis/type checker**: útil para enseñar tipos y localizar inconsistencias; puede ejecutarse localmente, sin cambiar archivos automáticamente.

## NOT NEEDED

- SQL/database tooling: no hay base de datos SQL demostrada.
- Deployment-provider integration: no se encontró proveedor ni configuración de despliegue.
- Broad write automation: aumenta riesgo y no aporta al aprendizaje inicial.
- Secret manager integration: no hace falta para leer el repositorio; si se añade operación remota, debe diseñarse aparte.

## Security boundary

`.env` está ignorado y contiene `DISCORD_TOKEN`, `BOT_OWNER_ID` y `PREMIUM_GUILD_IDS`; valores omitidos intencionalmente. No copiar `.env`, tokens, API keys, credenciales ni datos privados a `claude_context`. Cualquier herramienta con red o escritura remota necesita autorización explícita y mínimo privilegio.