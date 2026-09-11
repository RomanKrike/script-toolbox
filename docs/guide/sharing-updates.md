# Sharing and updates

Script Toolbox provides both local JSON portability and encrypted sharing through its share-provider abstraction.

## Import and export

Use JSON Import/Export when you want a file that can be archived, versioned, reviewed, or transferred manually.

Export is appropriate for:

- backups before large edits;
- storing a known-good toolbox configuration;
- moving a configuration between workstations;
- keeping example templates in source control.

Imported documents are validated against the configuration contract before they are accepted.

## Encrypted sharing

The sharing workflow can publish an encrypted toolbox configuration or supported item payload through the configured share provider. The provider abstraction keeps the UI and document layer independent from a specific paste service.

Use sharing for quick transfer when sending a file would be unnecessarily cumbersome. Use JSON Export when you need a durable artifact you control directly.

For implementation and security details, see [Sharing internals](../SHARING.md).

## Update channels

Script Toolbox supports selectable update channels:

| Channel | Intended use |
| --- | --- |
| Stable | Normal production use and published releases |
| Latest | Follow the newest appropriate published build |
| Development | Test the current `dev` state before release |

Stable releases are created from `main` after accumulated changes in `dev` have been tested and intentionally promoted.

## What the updater preserves

The updater downloads and verifies the plugin archive, replaces the installed package, and preserves user configuration stored outside the package. It then attempts a hot reload; restarting the host is the fallback when a safe reload cannot complete.

For implementation details, see [Updater internals](../UPDATER.md).

## Development builds

Development builds are for validating work that has not yet been released. Because Stable and Development use the same user-config location, export a backup before testing a risky or schema-changing development build.
