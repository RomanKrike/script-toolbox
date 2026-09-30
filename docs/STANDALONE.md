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

Maya, Nuke and Houdini continue to use their own Python/Qt runtimes and point at `scripts`. The standalone `ScriptToolbox.exe` is the real Windows GUI process: it loads the versioned Python DLL from `runtime` into its own process and invokes `standalone/bootstrap.py`. It does not spawn `python.exe` or `pythonw.exe` as the application process.

The launcher resolves all paths relative to its own executable location. It does not depend on the process current working directory. Before Qt is initialized it applies the explicit Windows AppUserModelID `ScriptToolbox.App`; the Python standalone entry point applies the same ID as a guarded fallback.

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
3. generates the Windows VERSIONINFO resource with ProductName/FileDescription `Script Toolbox`, InternalName `ScriptToolbox` and OriginalFilename `ScriptToolbox.exe`;
4. compiles the minimal native `standalone/launcher.c` plus that resource into `ScriptToolbox.exe`;
5. embeds `scripts/script_toolbox/resources/logo_sbt.ico` into the PE icon resources and verifies that the icon resource exists;
6. runs `tools/build_standalone_portable.py` to stage the runtime and the repository's single shared Script Toolbox source tree;
7. smoke-tests the shared UI lifecycle and starts the packaged `ScriptToolbox.exe` itself;
8. uploads the ZIP and SHA-256 file as workflow artifacts.

The resulting ZIP does not require an installer, administrator rights, a system Python installation, or a system Qt installation.

## User data

Standalone uses the existing `core/user_paths.py` path mechanism. Its host-specific default config filename is `script_toolbox.json`; DCC hosts retain their current filenames and locations. Existing schema-21 configs can be imported/opened without conversion because standalone uses the same config loader and schema.

## Limitations

DCC-specific Python code remains DCC-specific. For example, a script containing `import maya.cmds` will fail when executed by the standalone Python runtime. Standalone does not emulate DCC APIs or add a compatibility framework for such scripts.


## Windows taskbar smoke test

Taskbar pinning depends on Windows Shell state and is verified manually after a clean portable build:

1. Remove any old Script Toolbox/Python taskbar pin left by previous builds.
2. Start `ScriptToolbox.exe` from the freshly extracted portable package.
3. Right-click the active taskbar icon. The application entry should be `Script Toolbox`, not `Python`.
4. Choose **Pin to taskbar**, close Script Toolbox, then launch it from the pinned icon.
5. Confirm that the pinned target opens `ScriptToolbox.exe`, keeps the Script Toolbox icon and does not create a second Python taskbar group.

Explorer and the taskbar cache icons aggressively. If an old Python or previous Script Toolbox icon remains after replacing the EXE, unpin the old shortcut and pin the fresh executable again. Explorer may also need to refresh its icon cache; this is Shell cache behavior rather than an application identity fallback.
