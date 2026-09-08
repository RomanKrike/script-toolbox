# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.preferences import UPDATE_CHANNEL_DEVELOPMENT
from ..core.preferences import UPDATE_CHANNEL_STABLE
from ..core.preferences import get_update_channel
from ..core.preferences import normalize_update_channel
from ..core.preferences import set_update_channel
from .update_ui import UpdateCheckThread


_CHANNEL_LABELS = {
    UPDATE_CHANNEL_STABLE: "Stable",
    UPDATE_CHANNEL_DEVELOPMENT: "Development",
}


def build_update_channel_toolbox_class(
    base_class
):

    class UpdateChannelToolbox(base_class):

        def __init__(
            self,
            parent=None
        ):
            self.update_channel = get_update_channel()
            self._update_channel_actions = {}
            self._update_channel_button = None
            base_class.__init__(
                self,
                parent
            )

        def build_ui(self):
            base_class.build_ui(
                self
            )
            self._install_update_channel_menu()

        def _find_update_check_button(self):
            try:
                buttons = self.findChildren(
                    QtGui.QToolButton
                )
            except Exception:
                buttons = []

            for button in buttons:
                try:
                    tooltip = str(
                        button.toolTip()
                    )
                except Exception:
                    tooltip = ""

                if tooltip.startswith(
                    "Check for Script Toolbox updates"
                ):
                    return button

            return None

        def _install_update_channel_menu(self):
            button = self._find_update_check_button()

            if button is None:
                return

            menu = QtGui.QMenu(
                button
            )
            title_action = QtGui.QAction(
                "Update channel",
                menu
            )
            title_action.setEnabled(
                False
            )
            menu.addAction(
                title_action
            )
            menu.addSeparator()

            self._update_channel_actions = {}

            for channel in (
                UPDATE_CHANNEL_STABLE,
                UPDATE_CHANNEL_DEVELOPMENT,
            ):
                action = QtGui.QAction(
                    _CHANNEL_LABELS[
                        channel
                    ],
                    menu
                )
                action.setCheckable(
                    True
                )
                action.triggered.connect(
                    self._make_update_channel_handler(
                        channel
                    )
                )
                menu.addAction(
                    action
                )
                self._update_channel_actions[
                    channel
                ] = action

            button.setMenu(
                menu
            )
            button.setPopupMode(
                QtGui.QToolButton.MenuButtonPopup
            )

            self._update_channel_button = button
            self._refresh_update_channel_ui()

        def _make_update_channel_handler(
            self,
            channel
        ):
            def handler(
                checked=False
            ):
                self.set_update_channel(
                    channel
                )

            return handler

        def _refresh_update_channel_ui(self):
            channel = normalize_update_channel(
                self.update_channel
            )
            label = _CHANNEL_LABELS.get(
                channel,
                "Stable"
            )

            for value, action in self._update_channel_actions.items():
                action.setChecked(
                    value == channel
                )

            if self._update_channel_button is not None:
                self._update_channel_button.setToolTip(
                    (
                        "Check for Script Toolbox updates\n"
                        "Update channel: {0}\n"
                        "Use the arrow to change channel."
                    ).format(
                        label
                    )
                )

        def set_update_channel(
            self,
            channel
        ):
            channel = normalize_update_channel(
                channel
            )

            if channel == self.update_channel:
                self._refresh_update_channel_ui()
                return

            self.update_channel = set_update_channel(
                channel
            )
            self.update_info = None

            try:
                self.update_button.setVisible(
                    False
                )
            except Exception:
                pass

            self._refresh_update_channel_ui()

            self.statusBar().showMessage(
                "Update channel changed to {0}.".format(
                    _CHANNEL_LABELS[
                        self.update_channel
                    ]
                ),
                4000
            )

            self.check_for_updates(
                manual=True
            )

        def check_for_updates(
            self,
            manual=False
        ):
            if (
                self.update_check_thread is not None and
                self.update_check_thread.isRunning()
            ):
                return

            self._manual_update_check = bool(
                manual
            )

            if manual:
                self.statusBar().showMessage(
                    (
                        "Checking for Script Toolbox "
                        "{0} updates..."
                    ).format(
                        _CHANNEL_LABELS[
                            self.update_channel
                        ]
                    )
                )

            self.update_check_thread = UpdateCheckThread(
                self,
                channel=self.update_channel
            )
            self.update_check_thread.completed.connect(
                self.update_check_finished
            )
            self.update_check_thread.start()

        def update_check_finished(
            self,
            result
        ):
            result_channel = normalize_update_channel(
                result.get(
                    "channel"
                ),
                default=self.update_channel
            )

            if result_channel != self.update_channel:
                QtCore.QTimer.singleShot(
                    50,
                    self.check_for_updates
                )
                return

            base_class.update_check_finished(
                self,
                result
            )

    UpdateChannelToolbox.__name__ = (
        "ScriptToolbox"
    )
    return UpdateChannelToolbox


__all__ = [
    "build_update_channel_toolbox_class",
]
