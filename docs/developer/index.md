# Developer documentation

This section collects the existing implementation documentation for contributors, maintainers, and advanced debugging.

## Start here

- [Architecture](../ARCHITECTURE.md) — package boundaries, dependency direction, document/schema contracts, and host isolation.
- [Config store](../CONFIG_STORE.md) — persistence and configuration storage behavior.
- [Runtime renderer registry](../RUNTIME_RENDERER_REGISTRY.md) — runtime item renderer registration and contracts.
- [Host callbacks](../HOST_CALLBACKS.md) — host-specific callback integration.
- [Telemetry](../TELEMETRY.md) — telemetry design, consent, and implementation details.
- [Updater](../UPDATER.md) — update channels, package replacement, verification, and reload behavior.

Additional technical notes remain in the repository `docs/` directory even when they are not part of the primary site navigation. They document focused subsystems and regression contracts used during development.

## Branch model

Development is integrated in `dev`. Significant work should normally be developed in `feature/*` or `fix/*` branches based on `dev`, then merged back into `dev` for combined testing. `main` represents stable release state.

Documentation changes for unreleased functionality should therefore land with the corresponding development work rather than describing behavior that is not yet available in the relevant branch.
