# Dockable panels context

Branch: `feature/dcc-dockable-panels` from `origin/dev` `55235bb`. Parent Issue: #151. Stages: #152–#156.

Current design: `ui/debounced_main_window.py` owns the one active main window. The existing Runtime, ConfigStore, Item and Preset code remains shared. `ui/panel_container.py` is the QWidget passed to host APIs. It creates one child Runtime or an inert conflict message. Mode changes close the old Runtime after flushing pending data; no Qt widget is reparented between modes. A host-owned container is never directly deleted by the lifecycle controller.

Host entry points: Maya `integrations/maya_dock.py`; Houdini Package XML and `.pypanel` from `integrations/houdini.py`, with `houdini_integration.open_pane_tab`; Nuke `nuke_integration.register_panel` with stable Pane ID. `bootstrap.hot_reload_toolbox` reuses a live panel container.

Known limits: real DCC acceptance and real Qt are NOT RUN in this workspace. Need validate Maya 2015/2017/2024/2025, Houdini 19.5/20/21, and Nuke 12 directly. Verify workspace/Desktop restoration, Reload Scripts, and install/repair/uninstall in host before merge. CI on pushed SHA and code review remain required.

Next step: run full local tests, inspect lifecycle and host adapter diff, then push feature branch and inspect CI. Record real DCC results in #153–#156 before proposing merge.
