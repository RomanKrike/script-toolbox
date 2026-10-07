# Updater

Script Toolbox has two update channels: **Stable** reads the latest normal GitHub Release from `main`; **Development** reads the moving `dev-latest` prerelease from `dev`. Stable is the default. The updater chooses the plugin or Windows standalone package for the running installation.

## Update controls

- **Settings → Check for Updates** starts a manual check.
- **Settings → Update Channel → Stable / Development** changes the channel and checks it immediately.
- **Settings → Open Settings → General → Update channel** offers the same preference.

Checks run in a background QThread. An available update is shown as `UPDATE <version>` in the top bar; installation requires confirmation. Check/install failures are reported in the status bar or a dialog.

## Verified installation

The updater downloads the official ZIP and its matching `.sha256` through `core.http_transport`. The SHA-256 must match before recovery, extraction, staging or activation touches the installation. Missing package/checksum metadata or a failed verification stops installation. GitHub's generated **Source code** archives are not an installation fallback.

The installation path depends on the package:

| Package | Activation |
| --- | --- |
| DCC plugin | Stage and validate the shared package, activate it, then unload/reload Script Toolbox modules and reopen its UI. Restart the DCC if hot reload fails. |
| Windows standalone | Stage the portable package, close the application, and run an external helper that activates the update and restarts `ScriptToolbox.exe`. If an automatic restart cannot be scheduled, the UI requests a manual restart. |

Activation failures use transaction rollback/recovery. Portable updates track restart acknowledgement; they do not attempt to hot reload the active native Python/Qt runtime. User configuration and update-channel settings are preserved. See [Standalone](STANDALONE.md).

`core.update_transaction.install_release()` is the public production installation entry point; it routes portable work through `core.standalone_update`. `core.updater.install_release()` delegates to that entry point. Release metadata/archive utilities belong to `core.updater`; network execution belongs to `core.http_transport`.

## Stable release assets

For version 1.1.0, the stable release publishes:

| Package | Archive |
| --- | --- |
| DCC plugin | `script-toolbox-1.1.0.zip` |
| Windows standalone | `script-toolbox-1.1.0-standalone-windows-x64.zip` |

Each ZIP has its own `.zip.sha256` file. `release-build.json` records the source commit, version and hashes of both archives.

After successful push checks on `main`, `.github/workflows/release.yml` builds both packages from the checked commit. It verifies versions, checksums and matching shared source, creates the version tag, uploads all assets to a draft, then publishes the complete release. Pull request checks do not start automatic publication. An explicit workflow dispatch on `main` is also supported. Published versions are skipped rather than overwritten; prerelease versions such as `-dev` are skipped by this stable workflow.

## Development publication

Every push to `dev` runs `.github/workflows/dev-build.yml`. After Python checks pass, it builds both packages with the same development version and stamps build channel, run number and commit metadata. Both artifacts are verified before publication.

The `dev-latest` prerelease contains:

- immutable versioned plugin and standalone ZIPs, each with its checksum;
- plugin aliases `script-toolbox-dev.zip` and `script-toolbox-dev.zip.sha256`;
- standalone aliases `script-toolbox-standalone-dev.zip` and `script-toolbox-standalone-dev.zip.sha256`;
- `dev-manifest.json`, published last, which maps package kinds to the versioned assets and hashes.

The moving `dev-latest` tag is updated after complete publication. Stable uses GitHub's latest normal release endpoint, so this prerelease does not become a Stable update.

## Version comparison

Development build numbers increase with the workflow run number. An installed Development build receives an update when the published build number is higher. Switching from Stable to Development offers the current development build. Switching back to Stable uses semantic version comparison; a stable version ranks above its development prerelease with the same numeric version.

Both channels share the host's user configuration. Export a backup before testing changes to configuration schemas. Ordinary configs use schema 21; linked preset configs use schema 22 and require 1.1.0 or later. Older configs are not automatically migrated.

## Transport and proxy settings

Updater and encrypted sharing use the same network transport and **Settings → Open Settings → Network** preferences: System, No proxy or Manual (HTTP, HTTPS or SOCKS5, optional authentication).

On modern Windows, `urllib` is tried first, with hidden PowerShell/.NET fallback. Legacy Windows/Python 2 prefers PowerShell and falls back to `urllib`. Non-Windows uses `urllib`. PowerShell uses TLS 1.2 and explicit timeouts. Transport failures are normalized as `TransportError`/`UpdateError`.

Proxy passwords are protected with the user's DPAPI key on Windows. When no secure credential backend is available, passwords are not persisted. The public repository does not require a GitHub token. Private forks may use `SCRIPT_TOOLBOX_GITHUB_TOKEN`; it is read from the environment and is not stored in user settings or embedded in PowerShell command lines.
