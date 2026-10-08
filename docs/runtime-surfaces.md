# Runtime surface ownership and Apply

Apply prepares a complete Qt surface before saving the candidate document. A
surface owns its content widget, layout, value bindings and field/toggle widget
registrations. This is a GUI-thread operation; it does not move QWidget creation
to a worker or promise an atomic transaction spanning Qt and the filesystem.

| Phase | Owner and behavior | Failure result |
|---|---|---|
| Prepare | A hidden, disabled container and RuntimeSurfaceToolbox hold the candidate document and separate registration maps | Candidate bindings and widgets are disposed; active document, UI, file and editor delta are retained |
| Persist | Current authored document is checked again, then ConfigStore saves with the expected disk revision | Candidate is disposed; active state and editor delta are retained |
| Activate | Prepared container and maps replace the active surface; renderers are not called again | If the file was saved, reread the current disk document and show an inactive diagnostic surface; retain editor delta |
| Dispose | Previous surface disconnects owned bindings and releases its Qt tree | Stale callbacks cannot write through the disposed context |

Before these phases, pending changes are flushed and the editor delta is merged
against the current authored document. A renderer that reenters the application
and changes the current document causes a conflict before candidate persistence.
Disk revision checks still reject changes by another process.

If activation fails after persistence, recovery does **not** write the old
document back to disk: another process may already have written a newer document.
It reads the current document, updates the store revision, clears runtime maps,
pauses selection/state refresh and installs a diagnostic widget. The message
distinguishes successful persistence from failed UI activation. Reload rebuilds
the UI and resumes refresh. The editor is only reseeded after successful Apply.

Tab and radio selections are restored by section ID rather than by numeric
position; valid scroll positions are restored after Qt updates the layout. The
deferred restoration timer belongs to the new content widget and ignores a
surface that has been replaced.

## Renderer construction contract

During construction, `owner.toolbox` is a RuntimeSurfaceToolbox, not a
QMainWindow. It exposes candidate value reads, field display/refresh, toggle
presentation and widget/binding registration. State getter scripts are evaluated
after activation; preparation uses the stored value for initial presentation.

Create widgets with `owner.content` as their parent as early as possible. Parent
timers and QObject callbacks to that widget tree, and register value-edit
connections through the binding ownership API. A renderer must construct widgets
without saving, changing model values, dispatching item actions, modifying a DCC
scene, starting independent background work or calling `processEvents`.
Construction calls to save/store/action APIs through the context raise an error.

After activation, callbacks through the context forward to the actual Toolbox,
including its normal scripting and persistence API. This keeps callbacks bound
to the lifetime of the surface that created them. The context becomes inert when
disposed.

This contract does not sandbox arbitrary Python extensions. External side
effects, globally retained unparented widgets and subscriptions created outside
the declared ownership API remain the extension author's responsibility.

Regression coverage in `tests/test_qt_runtime_surface.py` exercises failures on
first/later items, write failure cleanup, post-save activation failure with a
concurrent disk edit, model writes during construction, reentrant changes, view
state restoration and delayed state-script evaluation. CI runs the real Qt
checks on Linux and Windows.
