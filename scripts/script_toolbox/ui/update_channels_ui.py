# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..core.preferences import UPDATE_CHANNEL_DEVELOPMENT
from ..core.preferences import UPDATE_CHANNEL_STABLE
from ..core.preferences import get_update_channel
from ..core.preferences import normalize_update_channel
from ..core.preferences import set_update_channel
from ..style import STYLE
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
            self._update_channel_menu = None
            base_class.__init__(
                self,
                parent
            )

        def build_ui(self):
            base_class.build_ui(
                self
            )
            self._install_update_channel_menu()

        def _install_update_channel_menu(self):
            settings_menu = getattr(
                self,
                "settings_menu",
                None
            )
            if settings_menu is None:
                return

            settings_menu.addSeparator()
            menu = settings_menu.addMenu(
                "Update Channel"
            )
            menu.setStyleSheet(
                STYLE
            )

            self._update_channel_actions = {}

            for channel in (
                UPDATE_CHANNEL_STABLE,
                UPDATE_CHANNEL_DEVELOPMENT,
            ):
                action = menu.addAction(
                    _CHANNEL_LABELS[
                        channel
                    ]
                )
                action.setCheckable(
                    True
                )
                action.triggered.connect(
                    self._make_update_channel_handler(
                        channel
                    )
                )
                self._update_channel_actions[
                    channel
                ] = action

            self._update_channel_menu = menu
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

            for value, action in self._update_channel_actions.items():
                action.setChecked(
                    value == channel
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
                        "Checking for {0} updates..."
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
