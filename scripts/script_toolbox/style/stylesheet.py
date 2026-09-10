# -*- coding: utf-8 -*-

from . import metrics
from . import palette


_STYLE_VALUES = dict(vars(palette))
_STYLE_VALUES.update(vars(metrics))


STYLE = """
/* ---------------------------------------------------------------
   Base
   --------------------------------------------------------------- */
QWidget {
    color: %(TEXT_PRIMARY)s;
    font-size: 11px;
}

QMainWindow,
QDialog {
    background-color: %(WINDOW_BG)s;
}

/* Runtime Toolbox containers.
   Keep backgrounds off generic QWidget/QCheckBox so Qt4 checkbox painting
   remains native and clean. */
QWidget#ToolboxCentral {
    background-color: %(CONTENT_BG)s;
}

QWidget#ToolboxContent {
    background-color: %(CONTENT_BG)s;
}

QFrame#RuntimeFolder {
    background-color: %(CONTENT_BG)s;
    border: 0px;
}

/* Collapsible folders are outlined cards at every hierarchy level.
   The header is visually attached to the same outline, so ownership of
   controls stays obvious even in long toolboxes. */
QFrame#RuntimeFolder[folderType="collapsible"] {
    background-color: %(FOLDER_CARD_BG)s;
    border: 1px solid %(SEPARATOR)s;
    border-radius: %(BORDER_RADIUS_CARD)spx;
}

QFrame#RuntimeFolder[folderType="collapsible"][nested="true"] {
    background-color: %(FOLDER_NESTED_BG)s;
    border-color: %(BORDER_FOLDER_NESTED)s;
}

/* Simple folders stay lightweight at top level, but nested Simple folders
   still work as visual subgroup cards. */
QFrame#RuntimeFolder[folderType="simple"][nested="true"] {
    background-color: %(FOLDER_NESTED_BG)s;
    border: 1px solid %(BORDER_FOLDER_NESTED)s;
    border-radius: %(BORDER_RADIUS_CARD)spx;
}

QWidget#RuntimeFolderContent {
    background-color: transparent;
}

/* Text labels should visually inherit the panel background. */
QLabel {
    background-color: transparent;
}

QToolTip {
    background-color: %(TOOLTIP_BG)s;
    color: %(TEXT_STRONG)s;
    border: 1px solid %(TOOLTIP_BORDER)s;
    padding: 4px;
}

/* ---------------------------------------------------------------
   Main toolbox header
   --------------------------------------------------------------- */
QFrame#TopBar {
    background-color: %(CONTROL_BG)s;
    border: 0px;
    border-bottom: 1px solid %(BORDER_TOPBAR)s;
}

QLabel#ToolboxTitle {
    background: transparent;
    color: %(TEXT_HEADING)s;
    font-weight: bold;
    padding-left: 4px;
}

QStatusBar {
    background-color: %(STATUS_BG)s;
    color: %(TEXT_STATUS)s;
    border-top: 1px solid %(BORDER_INSET)s;
}

/* ---------------------------------------------------------------
   Interface editor
   --------------------------------------------------------------- */
QLabel#DialogHeading {
    background-color: %(CONTROL_BG)s;
    color: %(TEXT_STRONG)s;
    font-weight: bold;
    font-size: 12px;
    border: 1px solid %(BORDER_INSET)s;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    padding: 7px 9px;
}

QWidget#EditorPane {
    background-color: %(PANEL_BG)s;
    border: 1px solid %(BORDER_PANEL)s;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
}

QScrollArea#PropertyScroll,
QWidget#PropertyViewport,
QWidget#PropertyHost,
QWidget#PropertyEditor {
    background-color: %(WINDOW_BG)s;
    border: 0px;
}

QLabel#PaneTitle {
    background-color: transparent;
    color: %(TEXT_PANE_TITLE)s;
    font-weight: bold;
    padding: 2px 1px 5px 1px;
}

QLabel#EditorStatus {
    background-color: transparent;
    color: %(TEXT_EDITOR_STATUS)s;
    padding-left: 2px;
}

QFormLayout QLabel {
    background-color: transparent;
}

QStackedWidget#PropertyStack {
    background-color: %(WINDOW_BG)s;
    border: 0px;
}

/* ---------------------------------------------------------------
   Folder headers in runtime toolbox
   --------------------------------------------------------------- */
QPushButton#RuntimeFolderHeader {
    background-color: %(FOLDER_HEADER_BG)s;
    color: %(TEXT_HEADING)s;
    border: 0px;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    min-height: 18px;
    padding: 2px 7px;
    font-weight: bold;
    text-align: left;
}

QPushButton#RuntimeFolderHeader:hover {
    background-color: %(FOLDER_HEADER_HOVER_BG)s;
    color: %(TEXT_FOLDER_HOVER)s;
}

QPushButton#RuntimeFolderHeader:pressed {
    background-color: %(FOLDER_HEADER_PRESSED_BG)s;
}

QPushButton#RuntimeFolderHeader[collapsed="true"] {
    background-color: %(FOLDER_HEADER_COLLAPSED_BG)s;
    color: %(TEXT_FOLDER_COLLAPSED)s;
}

/* Nested cards are deliberately quieter than primary sections. */
QFrame#RuntimeFolder[nested="true"] QPushButton#RuntimeFolderHeader {
    background-color: %(FOLDER_NESTED_HEADER_BG)s;
    color: %(TEXT_FOLDER_NESTED)s;
    min-height: 17px;
    padding: 2px 7px;
}

QFrame#RuntimeFolder[nested="true"] QPushButton#RuntimeFolderHeader:hover {
    background-color: %(FOLDER_NESTED_HEADER_HOVER_BG)s;
    color: %(TEXT_STRONG)s;
}

QFrame#RuntimeFolder[nested="true"] QPushButton#RuntimeFolderHeader[collapsed="true"] {
    background-color: %(FOLDER_NESTED_HEADER_COLLAPSED_BG)s;
    color: %(TEXT_SUBTLE)s;
}

QFrame#SimpleSectionHeader {
    background-color: transparent;
    border: 0px;
}

QFrame#RuntimeFolder[nested="true"] QFrame#SimpleSectionHeader {
    background-color: %(SIMPLE_SECTION_NESTED_BG)s;
    border: 0px;
    border-radius: %(BORDER_RADIUS_CONTROL)spx;
}

QLabel#SectionTitle {
    background: transparent;
    color: %(TEXT_SECTION)s;
    font-weight: bold;
    padding: 2px 3px 3px 3px;
}

QFrame#RuntimeFolder[nested="true"] QLabel#SectionTitle {
    color: %(TEXT_SECTION_NESTED)s;
    padding: 2px 4px 3px 4px;
}

QFrame#RuntimeSeparatorLine {
    background-color: %(SEPARATOR)s;
    border: 0px;
}

QFrame#RuntimeSeparatorLineVertical {
    background-color: %(SEPARATOR)s;
    border: 0px;
}

QWidget#RuntimeSeparatorContainer {
    background-color: transparent;
}

/* ---------------------------------------------------------------
   Buttons
   --------------------------------------------------------------- */
QPushButton,
QToolButton {
    background-color: %(BUTTON_BG)s;
    color: %(TEXT_BUTTON)s;
    border: 1px solid %(BORDER_PANEL)s;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    padding: %(BUTTON_PADDING_VERTICAL)spx %(BUTTON_PADDING_HORIZONTAL)spx;
}

QPushButton {
    min-height: %(BUTTON_MIN_HEIGHT)spx;
}

QPushButton:hover,
QToolButton:hover {
    background-color: %(BUTTON_HOVER_BG)s;
    border-color: %(HOVER_BORDER)s;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: %(BUTTON_PRESSED_BG)s;
    border-color: %(BORDER_PRESSED)s;
}

QPushButton:disabled,
QToolButton:disabled {
    color: %(TEXT_DISABLED)s;
    background-color: %(PANEL_BG)s;
    border-color: %(BORDER_DISABLED)s;
}

QToolButton#IconButton {
    background-color: transparent;
    border: 1px solid transparent;
    padding: 2px;
}

QToolButton#IconButton:hover {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    border-color: %(ICON_BUTTON_HOVER_BORDER)s;
}

QToolButton#IconButton:pressed {
    background-color: %(ICON_BUTTON_PRESSED_BG)s;
    border-color: %(BORDER_INSET)s;
}

QToolButton#UpdateButton {
    background-color: %(UPDATE_BG)s;
    color: %(TEXT_ON_ACCENT)s;
    border: 1px solid %(UPDATE_BORDER)s;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    padding: 3px 7px;
    font-weight: bold;
}

QToolButton#UpdateButton:hover {
    background-color: %(UPDATE_HOVER_BG)s;
    border-color: %(UPDATE_HOVER_BORDER)s;
}

QToolButton#UpdateButton:pressed {
    background-color: %(UPDATE_PRESSED_BG)s;
}

QToolButton#UpdateButton:disabled {
    background-color: %(UPDATE_DISABLED_BG)s;
    color: %(UPDATE_DISABLED_TEXT)s;
    border-color: %(UPDATE_DISABLED_BORDER)s;
}

QPushButton#AcceptButton {
    background-color: %(ACCEPT_BG)s;
    border-color: %(ACCEPT_BORDER)s;
    color: %(TEXT_ON_ACCENT)s;
    font-weight: bold;
}

QPushButton#AcceptButton:hover {
    background-color: %(ACCEPT_HOVER_BG)s;
    border-color: %(ACCEPT_HOVER_BORDER)s;
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
    background-color: %(CONTROL_BG)s;
    color: %(TEXT_INPUT)s;
    border: 1px solid %(BORDER_DARK)s;
    border-radius: %(BORDER_RADIUS_CONTROL)spx;
    selection-background-color: %(INPUT_SELECTION_BG)s;
    selection-color: %(TEXT_ON_ACCENT)s;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    min-height: %(INPUT_MIN_HEIGHT)spx;
    padding: %(INPUT_PADDING_VERTICAL)spx %(INPUT_PADDING_HORIZONTAL)spx;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid %(FOCUS_BORDER)s;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {
    background-color: %(WINDOW_BG)s;
    color: %(TEXT_INPUT_DISABLED)s;
    border-color: %(LIST_BG)s;
}

/* Keep the host-native ComboBox drop-down/arrow. Maya 2015 Qt4
   loses the arrow when QSS replaces these subcontrols. */

QComboBox QAbstractItemView {
    background-color: %(LIST_BG)s;
    color: %(TEXT_INPUT)s;
    border: 1px solid %(BORDER_DARK)s;
    selection-background-color: %(SELECTION_BG)s;
}

/* ---------------------------------------------------------------
   Lists / trees
   --------------------------------------------------------------- */
QListWidget,
QTreeWidget {
    background-color: %(LIST_BG)s;
    color: %(TEXT_LIST)s;
    border: 1px solid %(BORDER_PRESSED)s;
    border-radius: %(BORDER_RADIUS_CONTROL)spx;
    outline: 0px;
    alternate-background-color: %(LIST_ALT_BG)s;
}

QTreeWidget#ParameterPalette {
    background-color: %(LIST_BG)s;
    border-color: %(BORDER_SOFT)s;
    alternate-background-color: %(LIST_ALT_BG)s;
}

QListWidget::item,
QTreeWidget::item {
    min-height: %(LIST_ITEM_MIN_HEIGHT)spx;
    padding: %(LIST_ITEM_PADDING_VERTICAL)spx %(LIST_ITEM_PADDING_HORIZONTAL)spx;
    border: 0px;
}

QListWidget::item:hover,
QTreeWidget::item:hover {
    background-color: %(LIST_HOVER_BG)s;
}

QListWidget::item:selected,
QTreeWidget::item:selected {
    background-color: %(SELECTION_BG)s;
    color: %(SELECTION_TEXT)s;
}

QHeaderView::section {
    background-color: %(PANEL_BG)s;
    color: %(TEXT_HEADER)s;
    border: 0px;
    border-right: 1px solid %(CONTROL_BG)s;
    border-bottom: 1px solid %(BORDER_INSET)s;
    padding: 5px 6px;
    font-weight: bold;
}

/* ---------------------------------------------------------------
   Tabs
   --------------------------------------------------------------- */
QTabWidget::pane {
    background-color: %(WINDOW_BG)s;
    border: 1px solid %(BORDER_INSET)s;
    top: -1px;
}

QTabBar::tab {
    background-color: %(PANEL_BG)s;
    color: %(TEXT_TAB)s;
    border: 1px solid %(BORDER_TAB)s;
    border-bottom: 0px;
    padding: %(TAB_PADDING_VERTICAL)spx %(TAB_PADDING_HORIZONTAL)spx;
    margin-right: %(TAB_MARGIN_RIGHT)spx;
}

QTabBar::tab:hover {
    background-color: %(TAB_HOVER_BG)s;
    color: %(TEXT_INPUT)s;
}

QTabBar::tab:selected {
    background-color: %(TAB_SELECTED_BG)s;
    color: %(TEXT_TAB_SELECTED)s;
    border-top: 2px solid %(ACCENT)s;
}

/* Runtime folder tabs use the same visual contract as collapsible folder
   headers. Keep this scoped to toolbox content so editor tabs stay intact. */
QWidget#ToolboxContent QTabWidget::pane {
    background-color: %(FOLDER_CARD_BG)s;
    border: 1px solid %(SEPARATOR)s;
    border-radius: %(BORDER_RADIUS_CARD)spx;
    top: -1px;
}

QWidget#ToolboxContent QTabBar::tab {
    background-color: %(FOLDER_HEADER_COLLAPSED_BG)s;
    color: %(TEXT_FOLDER_COLLAPSED)s;
    border: 1px solid transparent;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    min-height: 18px;
    padding: 2px 7px;
    margin-right: %(TAB_MARGIN_RIGHT)spx;
    font-weight: bold;
}

QWidget#ToolboxContent QTabBar::tab:hover {
    background-color: %(FOLDER_HEADER_HOVER_BG)s;
    color: %(TEXT_FOLDER_HOVER)s;
    border-color: %(SEPARATOR)s;
}

QWidget#ToolboxContent QTabBar::tab:selected {
    background-color: %(FOLDER_HEADER_BG)s;
    color: %(TEXT_HEADING)s;
    border: 1px solid %(SEPARATOR)s;
    border-bottom-color: %(FOLDER_CARD_BG)s;
}

/* ---------------------------------------------------------------
   Group box
   --------------------------------------------------------------- */
QGroupBox {
    background-color: transparent;
    border: 1px solid %(BORDER_GROUP)s;
    border-radius: %(BORDER_RADIUS_PANEL)spx;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 5px;
    color: %(TEXT_SUBTLE)s;
}

/* ---------------------------------------------------------------
   Splitter / scroll
   --------------------------------------------------------------- */
QSplitter::handle {
    background-color: %(BORDER_INSET)s;
}

QScrollArea {
    border: 0px;
    background-color: transparent;
}

QScrollArea#ToolboxScroll {
    background-color: %(CONTENT_BG)s;
    border: 0px;
}

QScrollBar:vertical {
    background-color: %(LIST_BG)s;
    width: %(SCROLLBAR_EXTENT)spx;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: %(SCROLL_HANDLE_BG)s;
    min-height: %(SCROLLBAR_HANDLE_MINIMUM)spx;
    border-radius: %(BORDER_RADIUS_CARD)spx;
    margin: %(SCROLLBAR_HANDLE_MARGIN)spx;
}

QScrollBar::handle:vertical:hover {
    background-color: %(SCROLL_HANDLE_HOVER_BG)s;
}

QScrollBar:add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: %(LIST_BG)s;
    height: %(SCROLLBAR_EXTENT)spx;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: %(SCROLL_HANDLE_BG)s;
    min-width: %(SCROLLBAR_HANDLE_MINIMUM)spx;
    border-radius: %(BORDER_RADIUS_CARD)spx;
    margin: %(SCROLLBAR_HANDLE_MARGIN)spx;
}

QScrollBar::handle:horizontal:hover {
    background-color: %(SCROLL_HANDLE_HOVER_BG)s;
}

QScrollBar:add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}
""" % _STYLE_VALUES

__all__ = ["STYLE"]
