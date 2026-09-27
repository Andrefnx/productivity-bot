# Current State

Generated: 2026-09-26

## Git snapshot

- Branch: `v1.0`.
- Upstream: `origin/v1.0`; HEAD matches the shown upstream branch at audit time.
- Working tree: clean before creating this context package.
- Latest relevant commit: `815eebd` (`feat: implement active sprint status updates and recovery logic`, 2026-08-30).
- Earlier recent work includes project browser repair, timezone fixes and sprint lifecycle changes.

After this audit, the only intended new files are under `claude_context/`.

The current working tree also contains an uncommitted v1 patch: final sprint
results now show participants without word count in an unranked section, and
guild `1508950797344440509` is approved as premium by the entitlement check.

## Active systems

The active entry point, four slash commands, sprint lifecycle, profile/project workflows, JSON persistence, settings, help, import flow and tests are present. Economy functions are called by sprint result awarding and profile display. Marketplace modules are present but public reachability is not established.

## Incomplete or uncertain

- `marketplace` integration into the public command/navigation surface is UNKNOWN.
- No deployment configuration was found.
- Some legacy compatibility paths remain.
- Discord notification/recovery behavior depends on permissions and remote state.

## Test snapshot

`python -m unittest discover -s tests -p 'test_*.py'` ran 116 tests: 113 passed and 3 failed. The failures are timezone database/alias tests in `test_timezone_privacy.py` because this environment returned no usable zone list; this audit did not change code or dependencies. The run also printed a handled 403 warning from a sprint notification test path.

## Demonstrated risks, not fixes

- Runtime JSON files are local, synchronous and mutable; concurrent writes and corruption behavior should be considered before architectural changes.
- Discord API sends can fail with `Forbidden`/`HTTPException`; the current code catches/logs several cases but does not guarantee notification delivery.
- Project UI has Discord component limits such as 25 select options and 25 embed fields; existing project audit notes identify edge cases around large project lists.
- `.env` contains environment values and is ignored; values were intentionally not read into this package.

## TODO/FIXME

No general TODO/FIXME markers were found in tracked source. Legacy labels are compatibility terminology, not automatically planned work.