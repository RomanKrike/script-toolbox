# Updater

Script Toolbox uses GitHub Releases as the update channel.

## Runtime behavior

1. The main window starts an update check in a background QThread.
2. If the latest GitHub Release is newer than `PLUGIN_VERSION`, the top bar shows `UPDATE <version>`.
3. The user explicitly confirms installation.
4. The updater prefers the packaged `script-toolbox-<version>.zip` release asset.
5. If a SHA-256 asset is present, the downloaded ZIP is verified before extraction.
6. The current `scripts/script_toolbox` package is renamed to a temporary backup.
7. The new package is copied into place.
8. If copying fails, the old package is restored.
9. Maya restart is required after a successful update.

The Maya preferences config is outside the package and is not replaced.

## Releases

`scripts/script_toolbox/constants.py` contains:

```python
PLUGIN_VERSION = "0.2.0"
```

No manual tag is required.

After the stable version reaches `main`, the `Python checks` workflow runs first. If it succeeds, `.github/workflows/release.yml` automatically builds and validates the package, creates the matching `v0.2.0` tag when needed, and publishes the GitHub Release.

Versions containing a prerelease suffix such as `-dev` are skipped.

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
