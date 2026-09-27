# Development Rules

1. Inspect the existing code and call sites before proposing or editing behavior.
2. Use current code as the source of truth for current behavior; do not convert roadmap notes into requirements.
3. Make the smallest localized change that satisfies the explicit request.
4. Preserve existing behavior unless the user explicitly requests a behavior change.
5. Distinguish bug, feature request, cleanup, migration and documentation work.
6. Do not refactor unrelated modules during a feature or bug fix.
7. Do not delete or rename a View, callback, persistence key or exported function until all references are traced.
8. When changing a Discord interaction, check response timing, ownership checks, ephemeral/public visibility, View timeout and callback replacement paths.
9. When changing state, identify who creates it, who mutates it, when it is persisted, and what recovery does after restart.
10. Respect Discord limits: permissions, response acknowledgement, component options, embed fields and API failures.
11. Run the narrowest relevant tests/checks after each change and report unrelated baseline failures separately.
12. Explain important architectural decisions using real file/class/function names.
13. Never assume permission to commit, push, deploy, delete data or modify production.
14. Never expose `DISCORD_TOKEN`, API keys, credentials, `.env` values or private runtime data.
15. Treat `data/*.json` as runtime/user data; do not rewrite it for convenience.
16. Do not add dependencies unless explicitly requested; this context task added none.
17. Update context documents only when the code or documented intent actually changes.
18. If code and notes disagree, document both and label the disagreement UNKNOWN instead of guessing.
19. Prefer teaching the user to trace the next step before supplying a complete implementation when in Mentor Mode.
20. Keep `claude_context/` independent: application code must not import it.