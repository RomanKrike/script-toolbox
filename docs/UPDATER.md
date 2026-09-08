# Updater

Script Toolbox uses two GitHub-backed update channels:

- `Stable` reads the latest normal GitHub Release produced from `main`.
- `Development` reads the moving `dev-latest` prerelease produced from `dev`.

Stable remains the default.

## Runtime behavior

1. The main window starts an update check in a background QThread.
2. The selected update channel is loaded from `script_toolbox_settings.json`.
3. If an update is available, the top bar shows `UPDATE <version>`.
4. The user explicitly confirms installation.
5. The updater downloads the packaged ZIP for the selected channel.
6. If Maya 2015's Python 2.7 HTTPS stack cannot reach GitHub on Windows, the updater transparently falls back to PowerShell/.NET TLS 1.2 without opening a console window.
7. If a SHA-256 asset is present, the downloaded ZIP is verified before extraction.
8. The update is staged and validated before the live package is replaced.
9. If activation fails, the transaction restores the previous package.
10. The existing Toolbox UI is closed, all `script_toolbox.*` child modules are unloaded, the package root is reloaded in place, and the Toolbox reopens from the new files.
11. A DCC restart is only required as a fallback if hot reload fails or a future release introduces native binaries that cannot be unloaded safely.

The toolbox configuration is outside the package and is not replaced. Update-channel preferences are stored separately from `maya_script_toolbox.json`.

## Update channel UI

The Check for Updates tool button has a menu arrow.

The menu contains:

- `Stable`
- `Development`

Changing the channel persists the selection and immediately checks the newly selected channel.

## Stable releases

`scripts/script_toolbox/constants.py` contains the current semantic version, for example:

```python
PLUGIN_VERSION = "0.8.5"
```

After the stable version reaches `main`, the `Python checks` workflow runs first. If it succeeds, `.github/workflows/release.yml` builds and validates the package, creates the matching `v<version>` tag when needed, and publishes the GitHub Release.

Versions containing a prerelease suffix such as `-dev` are skipped by the stable release workflow.

## Development builds

Every push to `dev` runs `.github/workflows/dev-build.yml`.

The workflow calls the normal Python checks as a reusable workflow. Only after those checks succeed does it:

1. derive a development version such as `0.8.5-dev.42`;
2. stamp the package with `BUILD_CHANNEL = "development"`, the workflow build number, and the commit SHA;
3. build and checksum the package;
4. move the `dev-latest` tag to the tested commit;
5. create or update a single GitHub prerelease named `dev-latest`.

The prerelease always exposes the same three assets:

- `script-toolbox-dev.zip`
- `script-toolbox-dev.zip.sha256`
- `dev-manifest.json`

Old Development releases are not accumulated. The single `dev-latest` prerelease is updated in place.

The Stable updater uses GitHub's latest normal release endpoint, so the `dev-latest` prerelease does not become a Stable update.

## Development freshness

Development builds use the GitHub Actions run number as a monotonically increasing build number.

If the installed package is already a Development build, the updater offers a Development update only when the `dev-latest` build number is greater than the installed `BUILD_NUMBER`.

Switching from Stable to Development always offers the current `dev-latest` build. Switching from a Development build back to Stable uses the normal semantic-version comparison; a stable release with the same numeric version ranks above its development prerelease.

## Public repository

The repository is public, so update checks and release downloads do not require a GitHub token.

The updater still supports `SCRIPT_TOOLBOX_GITHUB_TOKEN` for compatibility with private forks. Tokens are read from the process environment only and are never written into the toolbox configuration or update settings.

## Manual update check

The top bar contains a manual Check for Updates button. Check failures are shown in the Toolbox status bar instead of being silently ignored.

## Failure behavior

Download and install failures are shown to the user, and the updater attempts to restore the previous package through the existing transaction mechanism.

If installation succeeds but hot reload fails, the new files remain installed and Script Toolbox asks the user to restart the host application.
