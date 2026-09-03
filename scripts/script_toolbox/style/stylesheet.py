# -*- coding: utf-8 -*-

STYLE = """
/* ---------------------------------------------------------------
   Base
   --------------------------------------------------------------- */
QWidget {
    color: #d6d6d6;
    font-size: 11px;
}

QMainWindow,
QDialog {
    background-color: #292929;
}

/* Runtime Toolbox containers.
   Keep backgrounds off generic QWidget/QCheckBox so Qt4 checkbox painting
   remains native and clean. */
QWidget#ToolboxCentral {
    background-color: #2b2b2b;
}

QWidget#ToolboxContent {
    background-color: #2b2b2b;
}

QFrame#RuntimeFolder {
    background-color: #2b2b2b;
    border: 0px;
}

/* Nested folders are real visual groups. The border makes it immediately
   obvious which controls belong to a subsection without making the whole
   toolbox look like a stack of heavy group boxes. */
QFrame#RuntimeFolder QFrame#RuntimeFolder {
    background-color: #282a2b;
    border: 1px solid #3b3d3f;
    border-radius: 4px;
}

QWidget#RuntimeFolderContent {
    background-color: transparent;
}

/* Text labels should visually inherit the panel background. */
QLabel {
    background-color: transparent;
}

QToolTip {
    background-color: #1d1d1d;
    color: #eeeeee;
    border: 1px solid #555555;
    padding: 4px;
}

/* ---------------------------------------------------------------
   Main toolbox header
   --------------------------------------------------------------- */
QFrame#TopBar {
    background-color: #202020;
    border: 0px;
    border-bottom: 1px solid #111111;
}

QLabel#ToolboxTitle {
    background: transparent;
    color: #e2e2e2;
    font-weight: bold;
    padding-left: 4px;
}

QStatusBar {
    background-color: #232323;
    color: #8f8f8f;
    border-top: 1px solid #171717;
}

/* ---------------------------------------------------------------
   Interface editor
   --------------------------------------------------------------- */
QLabel#DialogHeading {
    background-color: #202020;
    color: #eeeeee;
    font-weight: bold;
    font-size: 12px;
    border: 1px solid #171717;
    border-radius: 3px;
    padding: 7px 9px;
}

QWidget#EditorPane {
    background-color: #303030;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
}

QLabel#PaneTitle {
    background-color: transparent;
    color: #e0e0e0;
    font-weight: bold;
    padding: 2px 1px 5px 1px;
}

QLabel#HintText {
    background-color: transparent;
    color: #858585;
    font-size: 10px;
    padding: 5px 2px 1px 2px;
}

QLabel#EditorStatus {
    background-color: transparent;
    color: #8c8c8c;
    padding-left: 2px;
}

QFormLayout QLabel {
    background-color: transparent;
}

QStackedWidget#PropertyStack {
    background-color: #303030;
    border: 0px;
}

/* ---------------------------------------------------------------
   Folder headers in runtime toolbox
   --------------------------------------------------------------- */
QToolButton#RuntimeFolderHeader {
    background-color: #303235;
    color: #e2e2e2;
    border: 0px;
    border-left: 2px solid #8b603d;
    border-radius: 2px;
    min-height: 20px;
    padding: 2px 7px;
    font-weight: bold;
    text-align: left;
}

QToolButton#RuntimeFolderHeader:hover {
    background-color: #393c40;
    color: #f0f0f0;
    border-left-color: #b47543;
}

QToolButton#RuntimeFolderHeader:pressed {
    background-color: #292b2e;
}

QToolButton#RuntimeFolderHeader[collapsed="true"] {
    background-color: #2d2f31;
    color: #bdbdbd;
    border-left-color: #5f5147;
}

/* Nested collapsible groups live inside a card, so their own header is
   deliberately quieter than the top-level section header. */
QFrame#RuntimeFolder QFrame#RuntimeFolder QToolButton#RuntimeFolderHeader {
    background-color: #2e3031;
    color: #d7d7d7;
    border: 0px;
    border-bottom: 1px solid #3b3d3f;
    border-radius: 2px;
    min-height: 18px;
    padding: 2px 6px;
}

QFrame#RuntimeFolder QFrame#RuntimeFolder QToolButton#RuntimeFolderHeader:hover {
    background-color: #353738;
    color: #eeeeee;
    border-bottom-color: #4a4c4e;
}

QFrame#RuntimeFolder QFrame#RuntimeFolder QToolButton#RuntimeFolderHeader[collapsed="true"] {
    background-color: #2b2d2e;
    color: #bdbdbd;
    border-bottom-color: transparent;
}

QFrame#SimpleSectionHeader {
    background-color: transparent;
    border: 0px;
    border-bottom: 1px solid #3a3a3a;
}

/* Simple nested folders use the same card language as nested collapsibles. */
QFrame#RuntimeFolder QFrame#RuntimeFolder QFrame#SimpleSectionHeader {
    background-color: #2e3031;
    border: 0px;
    border-bottom: 1px solid #3b3d3f;
    border-radius: 2px;
}

QLabel#SectionTitle {
    background: transparent;
    color: #d2d2d2;
    font-weight: bold;
    padding: 2px 3px 3px 3px;
}

QFrame#RuntimeFolder QFrame#RuntimeFolder QLabel#SectionTitle {
    color: #d8d8d8;
    padding: 2px 4px 3px 4px;
}

/* ---------------------------------------------------------------
   Buttons
   --------------------------------------------------------------- */
QPushButton,
QToolButton {
    background-color: #3a3a3a;
    color: #dedede;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
    padding: 4px 8px;
}

QPushButton {
    min-height: 20px;
}

QPushButton:hover,
QToolButton:hover {
    background-color: #464646;
    border-color: #595959;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: #2f2f2f;
    border-color: #161616;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #686868;
    background-color: #303030;
    border-color: #252525;
}

QToolButton#IconButton {
    background-color: transparent;
    border: 1px solid transparent;
    padding: 2px;
}

QToolButton#IconButton:hover {
    background-color: #404040;
    border-color: #545454;
}

QToolButton#IconButton:pressed {
    background-color: #272727;
    border-color: #171717;
}

QToolButton#UpdateButton {
    background-color: #925426;
    color: #ffffff;
    border: 1px solid #b36b34;
    border-radius: 3px;
    padding: 3px 7px;
    font-weight: bold;
}

QToolButton#UpdateButton:hover {
    background-color: #a7622d;
    border-color: #cc7b3c;
}

QToolButton#UpdateButton:pressed {
    background-color: #7f4720;
}

QToolButton#UpdateButton:disabled {
    background-color: #4a4038;
    color: #8b827a;
    border-color: #55483e;
}

QPushButton#AcceptButton {
    background-color: #9a5826;
    border-color: #ba7139;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#AcceptButton:hover {
    background-color: #ad652d;
    border-color: #d18447;
}

QPushButton#ScriptButton {
    text-align: left;
    min-height: 26px;
    padding: 4px 9px;
}

/* ---------------------------------------------------------------
   Inputs
   --------------------------------------------------------------- */
QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QPlainTextEdit {
    background-color: #202020;
    color: #dddddd;
    border: 1px solid #151515;
    border-radius: 2px;
    selection-background-color: #8b572c;
    selection-color: #ffffff;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    min-height: 22px;
    padding: 2px 5px;
}

QLineEdit#PaletteFilter {
    background-color: #262626;
    border-color: #191919;
    min-height: 24px;
    padding-left: 7px;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid #78604a;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {
    background-color: #292929;
    color: #6f6f6f;
    border-color: #242424;
}

QComboBox::drop-down {
    border: 0px;
    width: 18px;
}

QComboBox QAbstractItemView {
    background-color: #242424;
    color: #dddddd;
    border: 1px solid #151515;
    selection-background-color: #68462c;
}

/* ---------------------------------------------------------------
   Lists / trees
   --------------------------------------------------------------- */
QListWidget,
QTreeWidget {
    background-color: #242424;
    color: #d4d4d4;
    border: 1px solid #161616;
    border-radius: 2px;
    outline: 0px;
    alternate-background-color: #282828;
}

QTreeWidget#ParameterPalette {
    background-color: #262626;
    border-color: #191919;
}

QListWidget::item,
QTreeWidget::item {
    min-height: 20px;
    padding: 3px 4px;
    border: 0px;
}

QListWidget::item:hover,
QTreeWidget::item:hover {
    background-color: #333333;
}

QListWidget::item:selected,
QTreeWidget::item:selected {
    background-color: #68462c;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #303030;
    color: #a8a8a8;
    border: 0px;
    border-right: 1px solid #202020;
    border-bottom: 1px solid #171717;
    padding: 5px 6px;
    font-weight: bold;
}

/* ---------------------------------------------------------------
   Tabs
   --------------------------------------------------------------- */
QTabWidget::pane {
    background-color: #292929;
    border: 1px solid #171717;
    top: -1px;
}

QTabBar::tab {
    background-color: #303030;
    color: #aaaaaa;
    border: 1px solid #1c1c1c;
    border-bottom: 0px;
    padding: 5px 11px;
    margin-right: 1px;
}

QTabBar::tab:hover {
    background-color: #393939;
    color: #dddddd;
}

QTabBar::tab:selected {
    background-color: #414141;
    color: #f0f0f0;
    border-top: 2px solid #b46d35;
}

/* ---------------------------------------------------------------
   Group box
   --------------------------------------------------------------- */
QGroupBox {
    background-color: transparent;
    border: 1px solid #414141;
    border-radius: 3px;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 5px;
    color: #bdbdbd;
}

/* ---------------------------------------------------------------
   Splitter / scroll
   --------------------------------------------------------------- */
QSplitter::handle {
    background-color: #171717;
}

QScrollArea {
    border: 0px;
    background-color: transparent;
}

QScrollArea#ToolboxScroll {
    background-color: #2b2b2b;
    border: 0px;
}

QScrollBar:vertical {
    background-color: #242424;
    width: 11px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    min-height: 24px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a5a;
}

QScrollBar:add-line:vertical,
QScrollBar:sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #242424;
    height: 11px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    min-width: 24px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5a5a5a;
}

QScrollBar:add-line:horizontal,
QScrollBar:sub-line:horizontal {
    width: 0px;
}
"""

__all__ = ["STYLE"]
