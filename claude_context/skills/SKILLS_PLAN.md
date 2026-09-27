# Skills Plan

No se creó una Skill ejecutable porque no se pudo verificar desde este repositorio el formato exacto soportado por el entorno objetivo de Claude. No se inventan archivos especiales. Estas propuestas pueden convertirse después al formato oficial.

## 1. Python Code Reading Mentor

- **Objetivo:** enseñar a leer un módulo real, tipos, imports, objetos, callers y mutaciones.
- **Trigger:** usuario pide entender código o aprender Python usando el bot.
- **Procedimiento:** localizar símbolo, seguir llamadas, separar Python/framework, preguntar el siguiente paso y validar comprensión.
- **Consultar:** `LEARNING_GUIDE.md`, `LEARNING_MAP.md`, `CODE_MAP.md`, archivo objetivo y tests.
- **Por qué merece Skill:** flujo pedagógico repetitivo y específico del proyecto.

## 2. Discord Interaction Trace

- **Objetivo:** reconstruir slash command -> View/Modal -> callback -> estado -> persistencia -> embed.
- **Trigger:** usuario pregunta cómo funciona un comando o interacción.
- **Procedimiento:** comenzar en `main.py` o el callback, identificar quién crea cada objeto y verificar respuesta/followup, permisos y timeout.
- **Consultar:** `ARCHITECTURE.md`, `CODE_MAP.md`, módulos y documentación oficial de discord.py.
- **Por qué:** reduce errores al explicar callbacks y async/event dispatch.

## 3. Sprint Flow Debugger

- **Objetivo:** diagnosticar una ruta de sprint sin refactorizarla.
- **Trigger:** bug, fallo de test o pregunta sobre join/leave/countdown/results/recovery.
- **Procedimiento:** reproducir con el test más estrecho, mapear timers y estado, revisar persistencia y errores Discord, proponer la menor corrección.
- **Consultar:** `CURRENT_STATE.md`, `ARCHITECTURE.md`, `modules/sprints/`, tests sprint y `sprint-audit` si está disponible como memoria.
- **Por qué:** los timers y callbacks cruzan varios módulos.

## 4. Context Synchronizer

- **Objetivo:** actualizar esta documentación después de cambios reales.
- **Trigger:** cambio de arquitectura, comando, persistencia o feature.
- **Procedimiento:** revisar diff, actualizar solo documentos afectados, mantener UNKNOWN y detectar contradicciones.
- **Consultar:** `README.md`, todos los documentos de contexto, código modificado, tests y Git read-only.
- **Por qué:** mantiene el mapa útil sin duplicar reglas de desarrollo.

No se proponen Skills separadas para “reglas de desarrollo” o “hacer features” porque esas responsabilidades ya están cubiertas por `DEVELOPMENT_RULES.md` y por el agente general.