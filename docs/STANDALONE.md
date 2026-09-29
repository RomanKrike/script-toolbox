# Standalone host

Script Toolbox can run as a normal host outside Maya, Nuke and Houdini. The standalone host reuses the same `scripts/script_toolbox` package, UI, item registry, bindings, config schema, templates and resources as the DCC hosts.

No standalone-only item type, launcher binding, script API or config schema is introduced. Existing `button` and `icon` items continue to execute their normal bindings. A Python binding can therefore launch another application with standard Python, for example `subprocess.Popen(...)`.

## Source layout

The portable package keeps one source tree:

```text
ScriptToolbox/
├── ScriptToolbox.exe
├── runtime/
├── scripts/
│   └── script_toolbox/
├── standalone/
│   └── bootstrap.py
├── MayaScriptToolbox.mod
├── nuke/
└── houdini/
```

Maya, Nuke and Houdini continue to use their own Python/Qt runtimes and point at `scripts`. `ScriptToolbox.exe` launches `runtime/pythonw.exe`, which runs `standalone/bootstrap.py`; the bootstrap then imports that same `scripts/script_toolbox` source tree.

The launcher resolves all paths relative to its own executable location. It does not depend on the process current working directory.

## Runtime lifecycle

The standalone entry point is:

```text
python -m script_toolbox.standalone
```

It resolves the existing Qt compatibility layer, creates a `QApplication` only when one does not already exist, calls the normal Script Toolbox `show()` bootstrap, then owns the Qt event loop until the window exits.

The explicit `StandaloneHost` inherits the safe defaults from `BaseHost`: Python is the only native script language, there is no DCC selection, no DCC main-window parent, and no emulation of Maya/Nuke/Houdini APIs.

## Portable build

`.github/workflows/standalone-build.yml` prepares a Windows x64 portable artifact. The workflow:

1. downloads the official Python embeddable runtime matching the selected Python 3.11 patch release;
2. installs PySide6 into that runtime only;
3. compiles the minimal native `standalone/launcher.c` into `ScriptToolbox.exe`;
4. runs `tools/build_standalone_portable.py` to stage the runtime and the repository's single shared Script Toolbox source tree;
5. uploads the ZIP and SHA-256 file as workflow artifacts.

The resulting ZIP does not require an installer, administrator rights, a system Python installation, or a system Qt installation.

## User data

Standalone uses the existing `core/user_paths.py` path mechanism. Its host-specific default config filename is `script_toolbox.json`; DCC hosts retain their current filenames and locations. Existing schema-21 configs can be imported/opened without conversion because standalone uses the same config loader and schema.

## Limitations

DCC-specific Python code remains DCC-specific. For example, a script containing `import maya.cmds` will fail when executed by the standalone Python runtime. Standalone does not emulate DCC APIs or add a compatibility framework for such scripts.
