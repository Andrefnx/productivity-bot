# Claude Context

Paquete de contexto derivado del repositorio `productivity-discord-bot`. Esta carpeta explica el comportamiento observable, los flujos reales y una forma de aprender Python leyendo este bot. No es una dependencia de la aplicación y no debe importarse desde `main.py`.

## Cómo usarlo

1. Leer este archivo.
2. Leer `PROJECT_CONTEXT.md` y `CURRENT_STATE.md` para una fotografía del producto.
3. Consultar `ARCHITECTURE.md` y `CODE_MAP.md` cuando una pregunta dependa de implementación.
4. Consultar `FEATURES.md` antes de llamar feature a algo existente.
5. Respetar `DEVELOPMENT_RULES.md` y `LEARNING_GUIDE.md` en cada sesión.
6. Usar `LEARNING_MAP.md` y `GLOSSARY.md` para mentoría.
7. Leer `CLAUDE_BOOTSTRAP.md` para iniciar una sesión nueva.

## Índice y autoridad

- `PROJECT_CONTEXT.md`: producto, alcance y vocabulario de alto nivel. Autoridad: síntesis derivada; el código decide el estado actual.
- `ARCHITECTURE.md`: arquitectura y flujos de ejecución reales. Autoridad: código actual, con referencias de archivos.
- `CODE_MAP.md`: mapa de módulos, llamadas, estado y dependencias. Autoridad: análisis del código actual.
- `FEATURES.md`: inventario por estado. Autoridad: código para implementación; notas para intención explícita.
- `CURRENT_STATE.md`: fotografía generada el 2026-09-26, Git, tests y riesgos observables. Autoridad: estado capturado durante esta auditoría.
- `DEVELOPMENT_RULES.md`: reglas de colaboración y seguridad para futuras sesiones. Autoridad: política de trabajo de este contexto.
- `LEARNING_GUIDE.md`: comportamiento de Claude en modo mentor y agente. Autoridad: acuerdo pedagógico de este contexto.
- `LEARNING_MAP.md`: conceptos de programación presentes o próximos, con ejemplos reales. Autoridad: inventario educativo derivado del código.
- `GLOSSARY.md`: términos del producto y de `discord.py` tal como se usan aquí.
- `CLAUDE_BOOTSTRAP.md`: prompt reutilizable para comenzar una sesión.
- `TOOLS_RECOMMENDATIONS.md`: herramientas externas evaluadas y permisos sugeridos.
- `skills/SKILLS_PLAN.md`: evaluación de Skills; no inventa un formato no verificado.

## Source of truth

- **Código actual**: verdad sobre lo que está implementado y cómo funciona ahora.
- **Documentación del proyecto** (`README.md`, `notes/`): intención o diseño solo cuando está explícitamente documentado.
- **`claude_context/`**: mapa y explicación derivados del análisis.

Si código y documentación contradicen algo, Claude debe señalar la contradicción y no inventar una resolución.