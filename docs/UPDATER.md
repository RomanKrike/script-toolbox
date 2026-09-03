# Updater

Script Toolbox uses GitHub Releases as the update channel.

## Runtime behavior

1. The main window starts an update check in a background QThread.
2. If the latest GitHub Release is newer than `PLUGIN_VERSION`, the top bar shows `UPDATE <version>`.
3. The user explicitly confirms installation.
4. The release ZIP is downloaded to a temporary directory.
5. The current `scripts/script_toolbox` package is renamed to a temporary backup.
6. The new package is copied into place.
7. If copying fails, the old package is restored.
8. Maya restart is required after a successful update.

The Maya preferences config is outside the package and is not replaced.

## Releases

`scripts/script_toolbox/constants.py` contains:

```python
PLUGIN_VERSION = "0.2.0"
```

Create a matching Git tag:

```text
v0.2.0
```

The `.github/workflows/release.yml` workflow validates that the tag matches `PLUGIN_VERSION` and creates the GitHub Release.

## Private repository

The repository is currently private. GitHub returns 404 to unauthenticated release requests for private repositories.

Set this environment variable before launching Maya:

```text
SCRIPT_TOOLBOX_GITHUB_TOKEN=<token>
```

The token is read from the process environment only. It is never written into `maya_script_toolbox.json`.

If the repository is public, no token is needed.

## Failure behavior

Update-check failures are intentionally silent: the Update button simply stays hidden.

Installation failures are shown to the user, and the updater attempts to restore the previous package from its temporary backup.
