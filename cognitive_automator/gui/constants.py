"""
gui/constants.py — Color palette, fonts, and shared style strings.
"""

from __future__ import annotations

# Node category colors
NODE_COLORS: dict[str, dict[str, str]] = {
    "physical": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#FFFFFF",
        "header_text": "#111827",
    },
    "vision": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#FFFFFF",
        "header_text": "#111827",
    },
    "llm": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#FFFFFF",
        "header_text": "#111827",
    },
    "flow": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#FFFFFF",
        "header_text": "#111827",
    },
    "logic": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#FFFFFF",
        "header_text": "#111827",
    },
    "system": {
        "bg": "#FFFFFF",
        "border": "#E5E7EB",
        "header": "#F3F4F6", # subtle distinction for system nodes
        "header_text": "#111827",
    },
}

NODE_CATEGORY_LABELS: dict[str, str] = {
    "physical": "Physical IO",
    "vision": "Vision",
    "llm": "LLM Logic",
    "flow": "Flow Control",
    "logic": "Programmatic Logic",
    "system": "System Markers",
}

# Application palette
APP_BG = "#FDFDFD"
APP_SURFACE = "#FFFFFF"
APP_SURFACE2 = "#F3F4F6"
APP_BORDER = "#E5E7EB"
APP_TEXT = "#111827"
APP_TEXT_DIM = "#6B7280"
APP_ACCENT = "#111827"  # Black accent for B&W theme
APP_SUCCESS = "#20C997"
APP_WARNING = "#FCC419"
APP_ERROR = "#FA5252"

MAIN_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {APP_BG};
    color: {APP_TEXT};
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
QMenuBar {{
    background-color: {APP_SURFACE2};
    color: {APP_TEXT};
    border-bottom: 1px solid {APP_BORDER};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {APP_BORDER};
}}
QMenu {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {APP_ACCENT};
    color: white;
}}
QToolBar {{
    background-color: {APP_SURFACE2};
    border-bottom: 1px solid {APP_BORDER};
    spacing: 4px;
    padding: 4px;
}}
QStatusBar {{
    background-color: {APP_SURFACE2};
    color: {APP_TEXT_DIM};
    border-top: 1px solid {APP_BORDER};
}}
QPushButton {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {APP_ACCENT};
    border-color: {APP_ACCENT};
    color: white;
}}
QPushButton:pressed {{
    background-color: #228BE6;
}}
QPushButton:disabled {{
    color: {APP_TEXT_DIM};
    border-color: {APP_BORDER};
    background-color: {APP_SURFACE2};
}}
QPushButton#danger {{
    border-color: {APP_ERROR};
    color: {APP_ERROR};
}}
QPushButton#danger:hover {{
    background-color: {APP_ERROR};
    color: white;
}}
QPushButton#success {{
    background-color: {APP_SUCCESS};
    color: white;
    border-color: {APP_SUCCESS};
    font-weight: bold;
}}
QPushButton#success:hover {{
    background-color: #12B886;
}}
QLineEdit {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {APP_ACCENT};
}}
QTextEdit, QPlainTextEdit, QTreeWidget, QListWidget {{
    background-color: {APP_SURFACE2};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {APP_ACCENT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTreeWidget:focus, QListWidget:focus {{
    border-color: {APP_ACCENT};
}}
QComboBox {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    min-width: 80px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    selection-background-color: {APP_ACCENT};
    border: 1px solid {APP_BORDER};
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 4px;
    padding: 5px;
}}
QLabel {{
    color: {APP_TEXT};
}}
QLabel#dim {{
    color: {APP_TEXT_DIM};
    font-size: 11px;
}}
QLabel#section {{
    color: {APP_ACCENT};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QScrollBar:vertical {{
    background: {APP_BG};
    width: 8px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {APP_BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {APP_TEXT_DIM};
}}
QSplitter::handle {{
    background: {APP_BORDER};
    width: 1px;
}}
QTabWidget::pane {{
    border: 1px solid {APP_BORDER};
    background: {APP_SURFACE};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {APP_SURFACE2};
    color: {APP_TEXT_DIM};
    padding: 8px 16px;
    border: 1px solid {APP_BORDER};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {APP_SURFACE};
    color: {APP_ACCENT};
    border-bottom: 2px solid {APP_ACCENT};
}}
QGroupBox {{
    border: 1px solid {APP_BORDER};
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    color: {APP_TEXT_DIM};
    font-size: 11px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
QSlider::groove:horizontal {{
    background: {APP_SURFACE2};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {APP_ACCENT};
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {APP_BORDER};
    border-radius: 3px;
    background: {APP_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {APP_ACCENT};
    border-color: {APP_ACCENT};
}}
"""

