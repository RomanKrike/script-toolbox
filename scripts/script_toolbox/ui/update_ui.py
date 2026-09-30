# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..core.update_channels import check_for_update
from ..core.update_transaction import install_release


class UpdateJobs(QtCore.QObject):
    """Application-owned workers survive window deletion and module reload."""
    def __init__(self, application):
        QtCore.QObject.__init__(self, application)
        self.jobs = set()
        application.aboutToQuit.connect(self.shutdown)

    def retain(self, job):
        self.jobs.add(job)
        job.finished.connect(self.release_finished)

    def release_finished(self):
        job = self.sender()
        self.jobs.discard(job)
        job.setParent(None)

    def shutdown(self):
        # Network operations have transport timeouts. Never terminate a worker
        # during a filesystem commit. No UI event processing during shutdown.
        for job in list(self.jobs):
            job.wait()


def update_jobs():
    application = QtCore.QCoreApplication.instance()
    if application is None:
        raise RuntimeError("Update jobs require a running Qt application.")
    owner = getattr(application, "_script_toolbox_update_jobs", None)
    if owner is None:
        owner = UpdateJobs(application)
        application._script_toolbox_update_jobs = owner
    return owner


class UpdateCheckThread(QtCore.QThread):

    completed = QtCore.Signal(
        object
    )

    def __init__(
        self,
        parent=None,
        channel="stable"
    ):
        owner = update_jobs()
        QtCore.QThread.__init__(self, owner)
        owner.retain(self)

        self.channel = channel

    def run(self):
        try:
            result = check_for_update(channel=self.channel)
        except Exception as exc:
            result = {"available": False, "error": str(exc), "channel": self.channel}
        self.completed.emit(result)


class UpdateInstallThread(QtCore.QThread):

    completed = QtCore.Signal(
        object
    )

    def __init__(
        self,
        release,
        parent=None
    ):
        owner = update_jobs()
        QtCore.QThread.__init__(self, owner)
        owner.retain(self)

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
