"""
=============================================================================
 STYLES.PY (base_components)
=============================================================================
This module is a microservice component for base_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.gui.constants import APP_ACCENT

PROPERTY_PANEL_STYLESHEET = f"""
#propPanel {{
    background-color: #111827;
    color: #FFFFFF;
}}
QScrollArea, QStackedWidget {{
    background-color: transparent;
    border: none;
}}
QLabel, QCheckBox {{
    color: #FFFFFF;
    background-color: transparent;
}}
QCheckBox::indicator {{
    background-color: #374151;
    border: 1px solid #4B5563;
    width: 14px;
    height: 14px;
    border-radius: 2px;
}}
QCheckBox::indicator:checked {{
    background-color: {APP_ACCENT};
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
    background-color: #1F2937;
    color: #FFFFFF;
    border: 1px solid #374151;
    padding: 4px;
    border-radius: 4px;
}}
QPushButton {{
    background-color: {APP_ACCENT};
    color: #000000;
    border: 2px solid #000000;
    border-right: 4px solid #000000;
    border-bottom: 4px solid #000000;
    border-radius: 0px;
    padding: 4px 12px;
    font-family: "Courier New";
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: #FFFFFF;
    color: #000000;
    border-color: #000000;
}}
QPushButton:pressed {{
    background-color: #FFFFFF;
    color: #000000;
    border-top: 4px solid #000000;
    border-left: 4px solid #000000;
    border-right: 2px solid #000000;
    border-bottom: 2px solid #000000;
}}
QSlider::groove:horizontal {{
    border: 1px solid #374151;
    height: 8px;
    background: #1F2937;
    margin: 2px 0;
    border-radius: 4px;
}}
QSlider::handle:horizontal {{
    background: {APP_ACCENT};
    border: 1px solid {APP_ACCENT};
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}}
QScrollBar:vertical {{
    background: #111827;
    width: 12px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {APP_ACCENT};
    min-height: 20px;
    border: none;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: #111827;
    height: 12px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {APP_ACCENT};
    min-width: 20px;
    border: none;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""
