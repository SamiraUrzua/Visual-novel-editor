from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

FONT_SIZE = 15

BG_DEEP    = "#13101e"
BG_BASE    = "#1a1628"
BG_PANEL   = "#221c34"
BG_INPUT   = "#2a2240"
BG_HOVER   = "#342850"
BG_SEL     = "#4a3580"

ACCENT     = "#9060ff"
ACCENT_DIM = "#5a3a90"
ACCENT_HI  = "#b890ff"

TEXT_HI    = "#f0ecff"
TEXT_MID   = "#c0aee0"
TEXT_DIM   = "#7a6898"
TEXT_MUTED = "#4a3a60"

BORDER     = "#3a2e58"
BORDER_DIM = "#241c3a"

# Buttons — clearly visible but not garish
BTN_DEFAULT  = "#2e2448"   # default: noticeably darker purple
BTN_PRIMARY  = "#5a2d90"   # aplicar: mid purple
BTN_DANGER   = "#5a1e2e"   # eliminar: dark red
BTN_NEW      = "#1a3d28"   # new/add: dark green
BTN_IO       = "#252040"   # io: muted purple

STYLESHEET = f"""
* {{
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: {FONT_SIZE}px;
}}

QWidget {{
    background-color: {BG_BASE};
    color: {TEXT_MID};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 10px;
    color: {TEXT_HI};
    selection-background-color: {ACCENT};
    selection-color: white;
    min-height: 32px;
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
    background-color: #302450;
}}

/* ── ComboBox popup only ── */
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    border: 1px solid {ACCENT_DIM};
    selection-background-color: {BG_SEL};
    selection-color: {TEXT_HI};
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 28px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {BTN_DEFAULT};
    border: 1px solid {ACCENT_DIM};
    border-radius: 5px;
    padding: 8px 16px;
    color: {TEXT_MID};
    font-weight: 600;
    min-height: 34px;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {ACCENT};
    color: {TEXT_HI};
}}
QPushButton:pressed {{
    background-color: {BG_SEL};
    color: white;
}}

QPushButton#btn_primary {{
    background-color: {BTN_PRIMARY};
    border-color: {ACCENT};
    color: {ACCENT_HI};
}}
QPushButton#btn_primary:hover {{
    background-color: #6e38aa;
    color: white;
}}

QPushButton#btn_danger {{
    background-color: {BTN_DANGER};
    border-color: #8a2a3e;
    color: #e07080;
}}
QPushButton#btn_danger:hover {{
    background-color: #7a2438;
    border-color: #e07080;
    color: #ffaaaa;
}}

QPushButton#btn_new {{
    background-color: {BTN_NEW};
    border-color: #2a6040;
    color: #70d090;
}}
QPushButton#btn_new:hover {{
    background-color: #204d30;
    border-color: #50b070;
    color: #a0f0b8;
}}

QPushButton#btn_io {{
    background-color: {BTN_IO};
    border-color: {BORDER};
    color: {TEXT_DIM};
}}
QPushButton#btn_io:hover {{
    background-color: {BTN_DEFAULT};
    border-color: {ACCENT_DIM};
    color: {TEXT_MID};
}}

/* ── Tree ── */
QTreeWidget {{
    background-color: {BG_DEEP};
    border: 1px solid {BORDER_DIM};
    border-radius: 6px;
    alternate-background-color: #171228;
    outline: none;
    show-decoration-selected: 1;
}}
QTreeWidget::item {{
    padding: 5px 6px;
    border-bottom: 1px solid #1e1830;
    min-height: 28px;
}}
QTreeWidget::item:selected {{
    background-color: {BG_SEL};
    color: {TEXT_HI};
}}
QTreeWidget::item:hover:!selected {{
    background-color: {BG_HOVER};
}}

QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {ACCENT};
    border: none;
    border-bottom: 2px solid {ACCENT_DIM};
    padding: 7px 10px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1.5px;
}}

/* ── Labels ── */
QLabel {{
    color: {TEXT_DIM};
    background: transparent;
}}
QLabel#lbl_section {{
    color: {ACCENT_HI};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 6px 0 2px 0;
}}
QLabel#lbl_cmd_type {{
    color: {TEXT_HI};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 0;
}}
QLabel#lbl_field {{
    color: {TEXT_DIM};
    font-size: 12px;
}}
QLabel#lbl_header {{
    color: {ACCENT_HI};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 8px 0 12px 0;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {BG_DEEP};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT_DIM};
    border-radius: 4px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}

/* ── Splitter ── */
QSplitter::handle {{ background-color: {ACCENT_DIM}; width: 2px; }}
QSplitter::handle:hover {{ background-color: {ACCENT}; }}

/* ── List ── */
QListWidget {{
    background-color: {BG_DEEP};
    border: 1px solid {BORDER_DIM};
    border-radius: 5px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid #1e1830;
    color: {TEXT_MID};
    min-height: 26px;
}}
QListWidget::item:selected {{ background-color: {BG_SEL}; color: {TEXT_HI}; }}
QListWidget::item:hover:!selected {{ background-color: {BG_HOVER}; }}

/* ── ScrollArea ── */
QScrollArea {{
    border: none;
    border-left: 2px solid {BORDER_DIM};
    background: {BG_PANEL};
}}
QScrollArea > QWidget > QWidget {{ background: {BG_PANEL}; }}
"""

def apply(app):
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", FONT_SIZE))