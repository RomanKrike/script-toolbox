# ScriptToolbox development

- Start with `CONTEXT.md`, the active GitHub Issue, `git status` and the relevant diff. Read only related code and docs.
- Keep feature work on `feature/dcc-dockable-panels` from `dev`; do not alter `main`, force-push, or merge before DCC acceptance.
- Preserve Python 2.7 syntax in shared runtime and support the host-selected PySide generation.
- One process owns one main ScriptToolbox Runtime. A second host pane may exist only as an inert container.
- Flush pending configuration before transitions or reload. Do not delete host-owned containers in their callbacks.
- Add tests for behavior and use fake host APIs only as contract checks. Mark real Maya/Houdini/Nuke scenarios NOT RUN until executed inside those hosts.
- Use `Refs #N` in atomic commits. Record CI SHA and manual results in Issues; close Issues only after acceptance.
