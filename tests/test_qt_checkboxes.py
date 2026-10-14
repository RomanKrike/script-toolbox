"""Checkbox appearance and interaction must survive native platform styles."""
from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_checkbox_palette_states_and_keyboard(tmp_path):
    run_qt('''
from script_toolbox.style import STYLE, palette
from script_toolbox.style.checkbox_assets import MARK_IMAGES
from PySide6.QtTest import QTest
import importlib
from script_toolbox.style import checkbox_assets, stylesheet
old_style = stylesheet.STYLE
old_images = dict(MARK_IMAGES)
importlib.reload(checkbox_assets)
importlib.reload(stylesheet)
assert checkbox_assets.MARK_IMAGES == old_images
assert stylesheet.STYLE == old_style
for path in MARK_IMAGES.values():
    assert not NativeGui.QPixmap(path).isNull(), path
for native_style in ("Fusion", "Windows"):
    app.setStyle(native_style)
    panel = QtGui.QWidget()
    panel.setStyleSheet(STYLE)
    layout = QtGui.QVBoxLayout(panel)
    checks = []
    for state in (QtCore.Qt.Unchecked, QtCore.Qt.Checked, QtCore.Qt.PartiallyChecked):
        check = QtGui.QCheckBox("Parameter", panel)
        check.setTristate(state == QtCore.Qt.PartiallyChecked)
        check.setCheckState(state)
        layout.addWidget(check)
        checks.append(check)
    panel.show()
    pump()
    for index, check in enumerate(checks):
        option = QtWidgets.QStyleOptionButton()
        check.initStyleOption(option)
        rect = check.style().subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator, option, check)
        assert rect.width() == 16 and rect.height() == 16, rect
        image = check.grab().toImage()
        # The mark is transparent at this corner: sample its fill, not its border.
        color = image.pixelColor(rect.left() + 3, rect.top() + 3).name()
        assert color == (palette.CONTROL_BG if index == 0 else palette.ACCENT), color
        if index:
            assert sum(image.pixelColor(x, y).name() == palette.TEXT_ON_ACCENT
                       for x in range(rect.left(), rect.right() + 1)
                       for y in range(rect.top(), rect.bottom() + 1)) > 5
        check.setEnabled(False)
        pump()
        image = check.grab().toImage()
        assert image.pixelColor(rect.left() + 3, rect.top() + 3).name() == palette.CONTROL_BG
        if index:
            assert sum(image.pixelColor(x, y).name() == palette.TEXT_DISABLED
                       for x in range(rect.left(), rect.right() + 1)
                       for y in range(rect.top(), rect.bottom() + 1)) > 5
    checks[0].setEnabled(True)
    checks[0].setFocus()
    QTest.keyClick(checks[0], QtCore.Qt.Key_Space)
    assert checks[0].isChecked()
    QTest.mouseClick(checks[0], QtCore.Qt.LeftButton, pos=QtCore.QPoint(7, checks[0].height() // 2))
    assert not checks[0].isChecked()
    panel.close()
    panel.deleteLater()
    pump()
w.close()
w.deleteLater()
pump()
''', tmp_path)
