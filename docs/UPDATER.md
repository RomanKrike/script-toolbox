# Updater

Script Toolbox uses GitHub Releases as the update channel.

## Runtime behavior

1. The main window starts an update check in a background QThread.
2. If the latest GitHub Release is newer than `PLUGIN_VERSION`, the top bar shows `UPDATE <version>`.
3. The user explicitly confirms installation.
4. The updater prefers the packaged `script-toolbox-<version>.zip` release asset.
5. If Maya 2015's Python 2.7 HTTPS stack cannot reach GitHub on Windows, the updater transparently falls back to PowerShell/.NET TLS 1.2 without opening a console window.
6. If a SHA-256 asset is present, the downloaded ZIP is verified before extraction.
7. The current `scripts/script_toolbox` package is renamed to a temporary backup.
8. The new package is copied into place.
9. If copying fails, the old package is restored.
10. The existing Toolbox UI is closed, all `script_toolbox.*` child modules are unloaded, the package root is reloaded in place, and the Toolbox reopens from the new files.
11. A Maya restart is only required as a fallback if hot reload fails or a future release introduces native binaries that cannot be unloaded safely.

The Maya preferences config is outside the package and is not replaced.

## Releases

`scripts/script_toolbox/constants.py` contains the current semantic version, for example:

```python
PLUGIN_VERSION = "0.2.4"
```

No manual tag is required.

After the stable version reaches `main`, the `Python checks` workflow runs first. If it succeeds, `.github/workflows/release.yml` automatically builds and validates the package, creates the matching `v<version>` tag when needed, and publishes the GitHub Release.

Versions containing a prerelease suffix such as `-dev` are skipped.

## Public repository

The repository is public, so update checks and release downloads do not require a GitHub token.

The updater still supports `SCRIPT_TOOLBOX_GITHUB_TOKEN` for compatibility with private forks. Tokens are read from the process environment only and are never written into `maya_script_toolbox.json`.

## Manual update check

The top bar contains a manual Check for Updates button. Check failures are shown in the Toolbox status bar instead of being silently ignored.

## Failure behavior

Download and install failures are shown to the user, and the updater attempts to restore the previous package from its temporary backup.

If installation succeeds but hot reload fails, the new files remain installed and Script Toolbox asks the user to restart Maya.
