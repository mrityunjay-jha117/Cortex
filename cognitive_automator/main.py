"""
main.py — Application entry point.
Sets up high-DPI, creates QApplication, launches MainWindow.
This is the entry point for command `python -m cognitive_automator`
"""

from __future__ import annotations
import sys
import os
import logging

"""
This is a customized logger.
It provides systematically tabulated logs in chronological order, 
along with their severity level.
For example, 
log.info("Cognitive Automator starting up.") will output:
13:45:10 INFO __main__ Cognitive Automator starting up.
The log will include the name of the caller. 
For instance, since it is called from main here, 
it will output __main__.
"""
def _configure_logging() -> None:
    if "--debug" in sys.argv :
        level=logging.DEBUG 
    else:
        level=logging.INFO    
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )    

"""Loads the environment variables and checks if the .env file is present. 
If it is missing, it gracefully handles the error by logging a warning instead of crashing."""
def _load_dotenv() -> None:
    """Load .env file using python-dotenv."""
    try:
        from dotenv import load_dotenv
        import pathlib
        root = pathlib.Path(__file__).parent.parent
        env_path = root / ".env"
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        import logging
        logging.getLogger(__name__).warning("python-dotenv not installed. Skipping .env loading.")


"""Sets up the basic instance of the GUI window, on top of which the widgets will be added."""
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

    # Must import Qt AFTER configuring the environment,
    # otherwise it will try to prematurely read the environment before setup is complete,
    # which will result in type errors.
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
    """
    The role of app.exec() is to handle the event loop. It always returns an integer.
    If it returns 1, it means an error caused the event loop to terminate.
    If it returns 0, it means everything exited successfully.
    sys.exit() uses this return code to gracefully shut down the application.
    """
    sys.exit(app.exec())

"""Resolves the accurate absolute path of files on your machine."""
def _resource_path(relative: str) -> str:
    
    # Development: assets are now inside the package folder
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


if __name__ == "__main__":
    main()
