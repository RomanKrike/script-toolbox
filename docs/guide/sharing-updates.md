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

After a shared payload is downloaded and decrypted, Script Toolbox checks it for executable Python/MEL behavior before changing the staged toolbox. Shares without executable content continue normally. Shares containing scripts, callbacks, event bindings, or state scripts require explicit **Import Anyway** confirmation; **Cancel** is the safe default and leaves the document/history unchanged.

Encryption authenticates the shared payload but does not make its scripts trusted. Review executable content and import it only from sources you trust.

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

The updater installs only the official Script Toolbox package asset paired with its `.sha256` asset. It downloads both files and verifies the archive SHA-256 before transaction recovery, extraction, staging, or activation can touch the live package. Missing or invalid checksums stop installation; GitHub source zipballs are not an installation fallback.

After verification, the transaction replaces the installed package while preserving user configuration stored outside the package. It then attempts a hot reload; restarting the host is the fallback when a safe reload cannot complete.

For implementation details, see [Updater internals](../UPDATER.md).

## Development builds

Development builds are for validating work that has not yet been released. Because Stable and Development use the same user-config location, export a backup before testing a risky or schema-changing development build.
