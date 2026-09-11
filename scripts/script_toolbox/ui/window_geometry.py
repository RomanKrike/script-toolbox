# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.window_geometry import get_window_geometry
from ..core.window_geometry import set_window_geometry


SAVE_DELAY_MS = 350
POST_SHOW_VALIDATE_MS = 200


def _desktop():
    try:
        application = QtGui.QApplication.instance()
        if application is None:
            return None
        return application.desktop()
    except Exception:
        return None


def _screen_count(desktop):
    if desktop is None:
        return 0

    try:
        return max(
            0,
            int(
                desktop.screenCount()
            )
        )
    except Exception:
        return 0


def _available_geometry(
    desktop,
    index
):
    try:
        return desktop.availableGeometry(
            int(index)
        )
    except Exception:
        return None


def _global_frame_rect(window):
    """Return the visible window frame in global desktop coordinates."""
    try:
        if window.isWindow():
            return QtCore.QRect(
                window.frameGeometry()
            )
    except Exception:
        pass

    try:
        top_left = window.mapToGlobal(
            QtCore.QPoint(
                0,
                0
            )
        )
        return QtCore.QRect(
            top_left.x(),
            top_left.y(),
            window.width(),
            window.height()
        )
    except Exception:
        return QtCore.QRect(
            window.geometry()
        )


def _intersection_area(
    first,
    second
):
    left = max(
        first.left(),
        second.left()
    )
    top = max(
        first.top(),
        second.top()
    )
    right = min(
        first.right(),
        second.right()
    )
    bottom = min(
        first.bottom(),
        second.bottom()
    )

    if right < left or bottom < top:
        return 0

    return (
        right - left + 1
    ) * (
        bottom - top + 1
    )


def _fallback_screen_index(
    desktop,
    window
):
    count = _screen_count(
        desktop
    )
    if count < 1:
        return None

    try:
        parent = window.parentWidget()
    except Exception:
        parent = None

    if parent is not None:
        try:
            index = int(
                desktop.screenNumber(
                    parent
                )
            )
            if 0 <= index < count:
                return index
        except Exception:
            pass

    try:
        index = int(
            desktop.primaryScreen()
        )
        if 0 <= index < count:
            return index
    except Exception:
        pass

    return 0


def _screen_index_for_rect(
    desktop,
    rect,
    window
):
    count = _screen_count(
        desktop
    )
    if count < 1:
        return None

    best_index = None
    best_area = 0

    for index in range(count):
        available = _available_geometry(
            desktop,
            index
        )
        if available is None:
            continue

        area = _intersection_area(
            rect,
            available
        )
        if area > best_area:
            best_area = area
            best_index = index

    if best_index is not None and best_area > 0:
        return best_index

    return _fallback_screen_index(
        desktop,
        window
    )


def _move_frame_top_left(
    window,
    x,
    y
):
    frame = _global_frame_rect(
        window
    )
    delta_x = int(x) - frame.left()
    delta_y = int(y) - frame.top()

    if delta_x == 0 and delta_y == 0:
        return False

    position = window.pos()
    window.move(
        position.x() + delta_x,
        position.y() + delta_y
    )
    return True


def _fit_window_to_screen(
    window,
    available
):
    frame = _global_frame_rect(
        window
    )

    extra_width = max(
        0,
        frame.width() - window.width()
    )
    extra_height = max(
        0,
        frame.height() - window.height()
    )

    max_width = max(
        1,
        available.width() - extra_width
    )
    max_height = max(
        1,
        available.height() - extra_height
    )

    width = min(
        window.width(),
        max_width
    )
    height = min(
        window.height(),
        max_height
    )

    try:
        width = max(
            min(
                int(window.minimumWidth()),
                max_width
            ),
            width
        )
        height = max(
            min(
                int(window.minimumHeight()),
                max_height
            ),
            height
        )
    except Exception:
        pass

    if (
        width != window.width() or
        height != window.height()
    ):
        window.resize(
            width,
            height
        )
        return True

    return False


def ensure_window_visible(window):
    """Clamp a floating toolbox window to a currently available screen."""
    desktop = _desktop()
    if desktop is None:
        return False

    frame = _global_frame_rect(
        window
    )
    screen_index = _screen_index_for_rect(
        desktop,
        frame,
        window
    )
    if screen_index is None:
        return False

    available = _available_geometry(
        desktop,
        screen_index
    )
    if available is None:
        return False

    _fit_window_to_screen(
        window,
        available
    )
    frame = _global_frame_rect(
        window
    )

    if frame.width() >= available.width():
        target_x = available.left()
    else:
        target_x = min(
            max(
                frame.left(),
                available.left()
            ),
            available.right() - frame.width() + 1
        )

    if frame.height() >= available.height():
        target_y = available.top()
    else:
        target_y = min(
            max(
                frame.top(),
                available.top()
            ),
            available.bottom() - frame.height() + 1
        )

    return _move_frame_top_left(
        window,
        target_x,
        target_y
    )


def restore_window_geometry(window):
    """Restore the persisted toolbox geometry and keep it fully on screen."""
    geometry = get_window_geometry()

    if geometry is not None:
        try:
            window.resize(
                geometry["width"],
                geometry["height"]
            )
            _move_frame_top_left(
                window,
                geometry["x"],
                geometry["y"]
            )
        except Exception:
            pass

    ensure_window_visible(
        window
    )
    return geometry is not None


def save_window_geometry(window):
    """Persist the current normal floating-window position and size."""
    try:
        if window.isMinimized() or window.isMaximized():
            return None
    except Exception:
        pass

    frame = _global_frame_rect(
        window
    )
    geometry = {
        "x": int(frame.left()),
        "y": int(frame.top()),
        "width": int(window.width()),
        "height": int(window.height()),
    }
    return set_window_geometry(
        geometry
    )


class WindowGeometryController(QtCore.QObject):
    """Debounced geometry persistence for one floating toolbox window."""

    def __init__(
        self,
        window
    ):
        QtCore.QObject.__init__(
            self,
            window
        )
        self.window = window
        self.enabled = False

        self.save_timer = QtCore.QTimer(
            self
        )
        self.save_timer.setSingleShot(
            True
        )
        self.save_timer.setInterval(
            SAVE_DELAY_MS
        )
        self.save_timer.timeout.connect(
            self.save_now
        )

        window.installEventFilter(
            self
        )

    def start(self):
        QtCore.QTimer.singleShot(
            0,
            self.restore
        )
        QtCore.QTimer.singleShot(
            POST_SHOW_VALIDATE_MS,
            self.validate_after_show
        )
        return self

    def restore(self):
        self.enabled = False
        try:
            restore_window_geometry(
                self.window
            )
        finally:
            self.enabled = True

    def validate_after_show(self):
        self.enabled = False
        try:
            restore_window_geometry(
                self.window
            )
        finally:
            self.enabled = True

    def schedule_save(self):
        if not self.enabled:
            return False
        self.save_timer.start()
        return True

    def save_now(self):
        self.save_timer.stop()
        if not self.enabled:
            return None
        try:
            return save_window_geometry(
                self.window
            )
        except Exception:
            return None

    def eventFilter(
        self,
        obj,
        event
    ):
        if obj is self.window:
            event_type = event.type()

            if event_type in (
                QtCore.QEvent.Move,
                QtCore.QEvent.Resize,
            ):
                self.schedule_save()
            elif event_type == QtCore.QEvent.Close:
                self.save_now()

        return QtCore.QObject.eventFilter(
            self,
            obj,
            event
        )


def install_window_geometry_persistence(window):
    if window is None:
        return None

    existing = getattr(
        window,
        "_window_geometry_controller",
        None
    )
    if existing is not None:
        return existing

    controller = WindowGeometryController(
        window
    )
    window._window_geometry_controller = controller
    controller.start()
    return controller


__all__ = [
    "POST_SHOW_VALIDATE_MS",
    "SAVE_DELAY_MS",
    "WindowGeometryController",
    "ensure_window_visible",
    "install_window_geometry_persistence",
    "restore_window_geometry",
    "save_window_geometry",
]
