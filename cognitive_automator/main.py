"""
main.py — Application entry point.

Sets up high-DPI, creates QApplication, launches MainWindow.
This is the entry point for both `python -m cognitive_automator` and the PyInstaller EXE.
"""

from __future__ import annotations

import sys
import os
import logging


def _configure_logging() -> None:
    level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_dotenv() -> None:
    """Load .env file from project root into os.environ (no external dep required)."""
    import pathlib
    root = pathlib.Path(__file__).parent.parent
    env_path = root / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def main() -> None:
    _load_dotenv()
    _configure_logging()
    log = logging.getLogger(__name__)
    log.info("Cognitive Automator starting up.")

    # High-DPI support for Windows
    if sys.platform == "win32":
        # Let Qt 6 handle awareness primarily to avoid conflicts
        # but ensure rounding is consistent for physical pixel libraries
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    # Must import Qt AFTER configuring environment
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon

    # High-DPI support for Qt
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Cognitive Automator")
    app.setOrganizationName("CognitiveAutomator")
    app.setApplicationVersion("1.0.0")

    # Try to set app icon (bundled in EXE via PyInstaller)
    icon_path = _resource_path("assets/icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    from cognitive_automator.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _resource_path(relative: str) -> str:
    """
    Get absolute path to a resource.
    Works both in development (relative to project root) and
    in a PyInstaller frozen EXE (relative to sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        # Running inside PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Development: assets are now inside the package folder
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


if __name__ == "__main__":
    main()
