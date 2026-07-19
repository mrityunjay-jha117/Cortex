"""
=============================================================================
 GUI CONSTANTS
=============================================================================
This module centrally defines all styling and layout constants for the UI.
It holds colors, fonts, dimensions, and theme settings.

Key Features:
1. Ensures consistent aesthetics across all widgets and canvas items.
2. Makes theme adjustments centralized and easy to update.

Think of this module as the style guide and color palette for the app.
=============================================================================
"""

from __future__ import annotations

# Node category colors
NODE_COLORS: dict[str, dict[str, str]] = {
    "physical": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "vision": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "llm": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "flow": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "logic": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
    },
    "system": {
        "bg": "#FFFFFF",
        "border": "#000000",
        "header": "#FFFFFF",
        "header_text": "#000000",
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
APP_BG = "#0B0F19"
APP_SURFACE = "#111827"
APP_SURFACE2 = "#1F2937"
APP_BORDER = "#374151"
APP_TEXT = "#F9FAFB"
APP_TEXT_DIM = "#9CA3AF"
APP_ACCENT = "#F7C76B"
APP_SUCCESS = "#10B981"
APP_WARNING = "#F59E0B"
APP_ERROR = "#EF4444"

MAIN_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {APP_BG};
    color: {APP_TEXT};
    font-family: "Courier New";
    font-size: 12px;
}}
#propPanel, #propPanel QScrollArea, #propPanel QStackedWidget, QWidget#propPanel, QWidget#propPage {{
    background-color: #333333;
}}
#propPanel QLabel, #propPanel QCheckBox, #propPanel QGroupBox, #propPanel QRadioButton {{
    color: #FFFFFF;
    font-weight: bold;
}}
#propPanel QLabel#section {{
    color: #FFFFFF;
    font-size: 14px;
    text-decoration: underline;
}}
#propPanel QGroupBox::title {{
    background-color: #333333;
    color: #FFFFFF;
}}
QMenuBar {{
    background-color: {APP_SURFACE2};
    color: {APP_TEXT};
    border-bottom: 2px solid {APP_BORDER};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {APP_ACCENT};
    color: #111827;
}}
QMenu {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 2px solid {APP_BORDER};
    border-radius: 0px;
}}
QMenu::item:selected {{
    background-color: {APP_ACCENT};
    color: #111827;
}}
QToolBar {{
    background-color: {APP_SURFACE2};
    border-bottom: 2px solid {APP_BORDER};
    spacing: 15px;
    padding: 10px;
}}
QToolBar QToolButton {{
    background-color: {APP_ACCENT};
    color: #000000;
    border: 2px solid #000000;
    border-right: 4px solid #000000;
    border-bottom: 4px solid #000000;
    border-radius: 0px;
    padding: 6px 12px;
    margin: 0px 4px;
    font-weight: bold;
}}
QToolBar QToolButton:hover {{
    background-color: #FDE49E;
    color: #000000;
}}
QToolBar QToolButton:pressed {{
    background-color: #E0AD4C;
    border-top: 4px solid #000000;
    border-left: 4px solid #000000;
    border-right: 2px solid #000000;
    border-bottom: 2px solid #000000;
    padding-top: 8px;
    padding-left: 14px;
    padding-bottom: 4px;
    padding-right: 10px;
}}
QStatusBar {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border-top: 1px solid {APP_BORDER};
}}
QRubberBand {{
    background-color: rgba(247, 199, 107, 80);
    border: 2px solid {APP_ACCENT};
}}
QPushButton {{
    background-color: {APP_ACCENT};
    color: #000000;
    border: 2px solid #000000;
    border-right: 4px solid #000000;
    border-bottom: 4px solid #000000;
    border-radius: 0px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: #FDE49E;
    color: #000000;
}}
QPushButton:pressed {{
    background-color: #E0AD4C;
    border-top: 4px solid #000000;
    border-left: 4px solid #000000;
    border-right: 2px solid #000000;
    border-bottom: 2px solid #000000;
    padding-top: 8px;
    padding-left: 18px;
    padding-bottom: 4px;
    padding-right: 14px;
}}
QPushButton:disabled {{
    color: {APP_TEXT_DIM};
    border: 2px dashed {APP_TEXT_DIM};
    background-color: {APP_BG};
}}
QPushButton#danger {{
    background-color: {APP_ERROR};
    color: #FFFFFF;
}}
QPushButton#danger:hover {{
    background-color: #F87171;
    color: #FFFFFF;
    border-color: #000000;
}}
QPushButton#danger:pressed {{
    background-color: #DC2626;
}}
QPushButton#success {{
    background-color: {APP_SUCCESS};
    color: #FFFFFF;
}}
QPushButton#success:hover {{
    background-color: #34D399;
    color: #FFFFFF;
    border-color: #000000;
}}
QPushButton#success:pressed {{
    background-color: #059669;
}}
QLineEdit {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 2px solid {APP_BORDER};
    border-radius: 0px;
    padding: 8px;
    selection-background-color: {APP_ACCENT};
    selection-color: {APP_SURFACE};
}}
QTextEdit, QPlainTextEdit, QTreeWidget, QListWidget {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 2px solid {APP_BORDER};
    border-radius: 0px;
    padding: 8px;
    selection-background-color: {APP_ACCENT};
    selection-color: {APP_SURFACE};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTreeWidget:focus, QListWidget:focus {{
    background-color: #F5F5F5;
    border: 2px solid {APP_ACCENT};
}}
QComboBox {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 2px solid {APP_BORDER};
    border-radius: 0px;
    padding: 5px 8px;
    min-width: 80px;
    font-weight: bold;
}}
QComboBox::drop-down {{
    border-left: 2px solid {APP_BORDER};
    width: 20px;
    background-color: {APP_SURFACE2};
}}
QComboBox QAbstractItemView {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    selection-background-color: {APP_ACCENT};
    selection-color: {APP_SURFACE};
    border: 2px solid {APP_BORDER};
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {APP_SURFACE};
    color: {APP_TEXT};
    border: 2px solid {APP_BORDER};
    border-radius: 0px;
    padding: 4px 6px;
    font-weight: bold;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 16px;
    border-left: 2px solid {APP_BORDER};
    background: {APP_SURFACE2};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {APP_TEXT_DIM};
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
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    background: {APP_BG};
    width: 12px;
    border-left: 2px solid {APP_BORDER};
}}
QScrollBar::handle:vertical {{
    background: {APP_BORDER};
    min-height: 20px;
    border: 1px solid {APP_SURFACE};
}}
QScrollBar::handle:vertical:hover {{
    background: {APP_ACCENT};
}}
QSplitter::handle {{
    background: {APP_BORDER};
    width: 2px;
}}
QTabWidget::pane {{
    border: 2px solid {APP_BORDER};
    background: {APP_SURFACE};
    border-radius: 0px;
}}
QTabBar::tab {{
    background: {APP_SURFACE2};
    color: {APP_TEXT};
    padding: 8px 16px;
    border: 2px solid {APP_BORDER};
    border-bottom: none;
    margin-right: 2px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {APP_SURFACE};
    color: {APP_ACCENT};
    border-top: 4px solid {APP_ACCENT};
}}
QGroupBox {{
    border: 2px solid {APP_ACCENT};
    border-radius: 0px;
    margin-top: 20px;
    padding-top: 15px;
    color: {APP_TEXT};
    font-size: 12px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    top: -10px;
    padding: 0 6px;
    background-color: {APP_BG};
    color: {APP_ACCENT};
}}
QSlider::groove:horizontal {{
    background: {APP_BORDER};
    height: 4px;
}}
QSlider::handle:horizontal {{
    background: {APP_ACCENT};
    border: 2px solid {APP_BORDER};
    width: 14px;
    height: 14px;
    margin: -7px 0;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {APP_BORDER};
    background: {APP_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {APP_ACCENT};
}}
"""

