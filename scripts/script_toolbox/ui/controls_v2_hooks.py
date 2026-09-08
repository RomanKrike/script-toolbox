# -*- coding: utf-8 -*-
from __future__ import print_function


_MAIN_WINDOW_MARKER = "_script_toolbox_controls_v2_main_window"
_TABS_MARKER = "_script_toolbox_controls_v2_tabs"
_RADIO_MARKER = "_script_toolbox_controls_v2_radio"


def _run_folder_callback(toolbox, folder, event, value, old_value):
    callback = getattr(
        toolbox,
        "run_item_callback",
        None
    )
    if callback is None:
        return None

    return callback(
        folder,
        event,
        value=value,
        old_value=old_value
    )


def _folder_page_changed(owner, index):
    folders = getattr(
        owner,
        "_script_toolbox_callback_folders",
        []
    )
    toolbox = getattr(
        owner,
        "_script_toolbox_callback_toolbox",
        None
    )
    previous = getattr(
        owner,
        "_script_toolbox_callback_index",
        -1
    )

    if index == previous:
        return

    if (
        toolbox is not None and
        0 <= previous < len(folders)
    ):
        _run_folder_callback(
            toolbox,
            folders[previous],
            "on_close",
            False,
            True
        )

    owner._script_toolbox_callback_index = index

    if (
        toolbox is not None and
        0 <= index < len(folders)
    ):
        _run_folder_callback(
            toolbox,
            folders[index],
            "on_open",
            True,
            False
        )


def _install_tabs_hook(runtime_module):
    tabs_class = runtime_module.RuntimeFolderTabs
    if getattr(tabs_class, _TABS_MARKER, False):
        return

    legacy_init = tabs_class.__init__

    def controls_v2_init(
        self,
        toolbox,
        folders,
        parent=None
    ):
        legacy_init(
            self,
            toolbox,
            folders,
            parent
        )
        self._script_toolbox_callback_toolbox = toolbox
        self._script_toolbox_callback_folders = list(folders)
        self._script_toolbox_callback_index = self.tabs.currentIndex()
        self.tabs.currentChanged.connect(
            lambda index:
            _folder_page_changed(
                self,
                index
            )
        )

    tabs_class.__init__ = controls_v2_init
    setattr(
        tabs_class,
        _TABS_MARKER,
        True
    )


def _install_radio_hook(runtime_module):
    radio_class = runtime_module.RuntimeFolderRadio
    if getattr(radio_class, _RADIO_MARKER, False):
        return

    legacy_init = radio_class.__init__

    def controls_v2_init(
        self,
        toolbox,
        folders,
        parent=None
    ):
        legacy_init(
            self,
            toolbox,
            folders,
            parent
        )
        self._script_toolbox_callback_toolbox = toolbox
        self._script_toolbox_callback_folders = list(folders)
        self._script_toolbox_callback_index = self.stack.currentIndex()
        self.stack.currentChanged.connect(
            lambda index:
            _folder_page_changed(
                self,
                index
            )
        )

    radio_class.__init__ = controls_v2_init
    setattr(
        radio_class,
        _RADIO_MARKER,
        True
    )


def _install_main_window_hook(main_window_class):
    if getattr(
        main_window_class,
        _MAIN_WINDOW_MARKER,
        False
    ):
        return

    legacy_refresh = main_window_class.refresh_state_button

    def refresh_state_button(self, key):
        result = legacy_refresh(
            self,
            key
        )
        item = self.find_item(key)

        if (
            item is not None and
            item.get("kind") == "button" and
            item.get("icon_only", False)
        ):
            widget = self.state_button_widgets.get(
                item.get("id")
            )
            if widget is not None:
                widget.setText("")

        return result

    main_window_class.refresh_state_button = refresh_state_button
    setattr(
        main_window_class,
        _MAIN_WINDOW_MARKER,
        True
    )


def install_controls_v2_hooks(
    runtime_module,
    main_window_class
):
    _install_tabs_hook(runtime_module)
    _install_radio_hook(runtime_module)
    _install_main_window_hook(main_window_class)
    return True


__all__ = [
    "install_controls_v2_hooks",
]
