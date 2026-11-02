"""Contract for the script embedded in Houdini's Python Panel interface."""
import sys
from types import ModuleType
from xml.etree import ElementTree

from script_toolbox.integrations.houdini import HoudiniAdapter


def _panel_script(monkeypatch, panel_class):
    script = ElementTree.fromstring(HoudiniAdapter._panel_content()).find(
        ".//script"
    ).text
    panel_module = ModuleType("script_toolbox.ui.panel_container")
    panel_module.ScriptToolboxPanel = panel_class
    monkeypatch.setitem(sys.modules, panel_module.__name__, panel_module)

    class Widget(object):
        def __init__(self, parent=None):
            self.parent = parent
            self._layout = None
            self.shown = False
            self.deleted = False

        def layout(self):
            return self._layout

        def show(self):
            self.shown = True

        def deleteLater(self):
            self.deleted = True

    class Label(Widget):
        def __init__(self, message, parent=None):
            Widget.__init__(self, parent)
            self.message = message

        def setWordWrap(self, value):
            self.word_wrap = value

    class Layout(object):
        def __init__(self, parent):
            parent._layout = self
            self.widgets = []

        def setContentsMargins(self, *args):
            pass

        def addWidget(self, widget):
            self.widgets.append(widget)

        def count(self):
            return len(self.widgets)

        def takeAt(self, index):
            widget = self.widgets.pop(index)
            return type("Item", (), {"widget": lambda self: widget})()

    class Signal(object):
        def connect(self, callback):
            self.callback = callback

    class Timer(object):
        def __init__(self, parent):
            self.parent = parent
            self.timeout = Signal()
            self.started = False

        def setSingleShot(self, value):
            pass

        def start(self, delay):
            self.started = True

        def stop(self):
            self.started = False

        def fire(self):
            if self.started:
                self.started = False
                self.timeout.callback()

    hutil = ModuleType("hutil")
    hutil.__path__ = []
    hutil_qt = ModuleType("hutil.Qt")
    hutil_qt.QtCore = type("Core", (), {"QTimer": Timer})
    hutil_qt.QtWidgets = type("Widgets", (), {
        "QWidget": Widget, "QLabel": Label, "QVBoxLayout": Layout
    })
    monkeypatch.setitem(sys.modules, "hutil", hutil)
    monkeypatch.setitem(sys.modules, "hutil.Qt", hutil_qt)

    namespace = {}
    exec(compile(script, "script_toolbox.pypanel", "exec"), namespace)
    return namespace


def test_panel_import_waits_until_houdini_activates_interface(monkeypatch):
    created = []

    class Panel(object):
        def __init__(self, parent):
            self.parent = parent
            self.shown = False
            created.append(self)

        def show(self):
            self.shown = True

    namespace = _panel_script(monkeypatch, Panel)
    root = namespace["onCreateInterface"]()
    assert created == []
    assert root.layout().widgets[0].message == "Loading ScriptToolbox..."

    namespace["onActivateInterface"]()
    namespace["_script_toolbox_timer"].fire()
    assert len(created) == 1
    assert created[0].parent is root
    assert created[0].shown
    assert root.layout().widgets == created

    namespace["onDestroyInterface"]()
    assert namespace["_script_toolbox_root"] is None


def test_panel_creation_error_is_visible_and_destroy_is_safe(monkeypatch):
    class BrokenPanel(object):
        def __init__(self, parent):
            raise RuntimeError("pane construction failed")

    namespace = _panel_script(monkeypatch, BrokenPanel)
    root = namespace["onCreateInterface"]()
    namespace["onActivateInterface"]()
    namespace["_script_toolbox_timer"].fire()
    label = root.layout().widgets[0]
    assert label.message.endswith("pane construction failed")
    assert label.word_wrap is True
    namespace["onDestroyInterface"]()


def test_destroy_before_activation_cancels_deferred_load(monkeypatch):
    class BrokenPanel(object):
        def __init__(self, parent):
            raise AssertionError("must not import after destroy")

    namespace = _panel_script(monkeypatch, BrokenPanel)
    namespace["onCreateInterface"]()
    timer = namespace["_script_toolbox_timer"]
    namespace["onActivateInterface"]()
    namespace["onDestroyInterface"]()
    timer.fire()
    assert namespace["_script_toolbox_widget"] is None
