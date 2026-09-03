# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..core.updater import check_for_update
from ..core.updater import install_release


class UpdateCheckThread(QtCore.QThread):

    completed = QtCore.Signal(
        object
    )

    def run(self):
        self.completed.emit(
            check_for_update()
        )


class UpdateInstallThread(QtCore.QThread):

    completed = QtCore.Signal(
        object
    )

    def __init__(
        self,
        release,
        parent=None
    ):
        QtCore.QThread.__init__(
            self,
            parent
        )

        self.release = release

    def run(self):
        try:
            result = install_release(
                self.release
            )
        except Exception as exc:
            result = {
                "installed": False,
                "error": str(
                    exc
                ),
            }

        self.completed.emit(
            result
        )


__all__ = [
    "UpdateCheckThread",
    "UpdateInstallThread",
]
