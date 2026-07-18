# -*- mode: python ; coding: utf-8 -*-
#
# CognitiveAutomator.spec
#
# Build with:
#   pyinstaller CognitiveAutomator.spec
#
# Output: dist/CognitiveAutomator.exe  (~80MB single file)
#

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ---------------------------------------------------------------------------
# Hidden imports — packages that PyInstaller can't auto-detect
# ---------------------------------------------------------------------------

hidden_imports = [
    # PyQt6
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.sip",
    # pynput backends
    "pynput.mouse._win32",
    "pynput.keyboard._win32",
    # OpenCV
    "cv2",
    # PIL
    "PIL",
    "PIL.Image",
    "PIL.ImageGrab",
    # pyautogui internals
    "pyautogui",
    "pygetwindow",
    "pyscreeze",
    "mouseinfo",
    # LLM clients (OpenRouter uses openai library)
    "openai",
    "openai._client",
    "requests",
    # Jinja2
    "jinja2",
    "jinja2.ext",
    # Pydantic
    "pydantic",
    "pydantic.v1",
    "pydantic_core",
    # networkx
    "networkx",
    "networkx.algorithms",
    "networkx.generators",
    # yaml
    "yaml",
    # pyperclip
    "pyperclip",
    # tenacity
    "tenacity",
    # Windows-specific
    "win32api",
    "win32con",
    "win32gui",
]

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------

datas = [
    # Application assets (now inside package)
    ("cognitive_automator/assets", "assets"),
]

# Collect PyQt6 Qt platform plugins (essential for the EXE to render)
try:
    from PyInstaller.utils.hooks import collect_dynamic_libs
    binaries = collect_dynamic_libs("PyQt6")
except Exception:
    binaries = []

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(
    ["cognitive_automator/main.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy unused packages to keep EXE lean
        "matplotlib",
        "scipy",
        "pandas",
        "numpy.testing",
        "tkinter",       # replaced by PyQt6
        "test",
        "unittest",
        "pytest",
        "IPython",
        "notebook",
        # Exclude unused PyQt6 modules to suppress "Library not found" warnings
        "PyQt6.Qt3DCore",
        "PyQt6.Qt3DRender",
        "PyQt6.Qt3DInput",
        "PyQt6.Qt3DAnimation",
        "PyQt6.Qt3DExtras",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineQuick",
        "PyQt6.QtWebView",
        "PyQt6.QtQuick",
        "PyQt6.QtQuickWidgets",
        "PyQt6.QtSql",
        "PyQt6.QtBluetooth",
        "PyQt6.QtMultimedia",
        "PyQt6.QtDesigner",
        "PyQt6.QtHelp",
        "PyQt6.QtTest",
        "PyQt6.QtScxml",
        "PyQt6.QtQml",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ---------------------------------------------------------------------------
# PYZ archive
# ---------------------------------------------------------------------------

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# EXE (onefile mode)
# ---------------------------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CognitiveAutomator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # UPX compression — reduces EXE size ~30%
    upx_exclude=[
        # Exclude DLLs that UPX can corrupt
        "vcruntime*.dll",
        "msvcp*.dll",
        "Qt6*.dll",
    ],
    runtime_tmpdir=None,
    console=False,      # No console window — GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific
    version="version_info.txt",   # Windows file version metadata
    icon="cognitive_automator/assets/icon.ico",        # Application icon
    uac_admin=False,               # Do NOT require admin (pynput works without it)
)
