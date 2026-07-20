"""
=============================================================================
 STYLESHEET.PY (constants_components)
=============================================================================
This module is a microservice component for constants_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .colors import APP_BG, APP_SURFACE, APP_SURFACE2, APP_BORDER, APP_TEXT, APP_TEXT_DIM, APP_ACCENT, APP_SUCCESS, APP_WARNING, APP_ERROR

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
    background-color: #222222;
    color: #FFFFFF;
    border: 4px solid #000000;
    padding: 8px;
}}
QMenu::item {{
    background-color: {APP_ACCENT};
    color: #000000;
    padding: 8px 24px 8px 16px;
    margin: 4px 2px;
    font-weight: bold;
    border: 2px solid #000000;
    border-right: 4px solid #000000;
    border-bottom: 4px solid #000000;
}}
QMenu::item:selected {{
    background-color: #FFFFFF;
}}
QMenu::item:pressed {{
    background-color: #E0AD4C;
    border-top: 4px solid #000000;
    border-left: 4px solid #000000;
    border-right: 2px solid #000000;
    border-bottom: 2px solid #000000;
    padding: 10px 22px 6px 18px;
}}
QMenu#canvasMenu::item {{
    background-color: #FFFFFF;
}}
QMenu#canvasMenu::item:selected {{
    background-color: #F0F0F0;
}}
QMenu#canvasMenu::item:pressed {{
    background-color: #E0E0E0;
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
    background: {APP_ACCENT};
    width: 16px;
    
}}
QScrollBar::handle:vertical {{
    min-height: 20px;
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
