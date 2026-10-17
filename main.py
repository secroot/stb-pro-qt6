"""
STB Pro v6.0 — Qt6 / PySide6 Edition Entry Point.
Initializes High-DPI scaling, applies the Obsidian Cyber-Cinema dark theme,
and launches the main application window.
"""
import os
import sys

# Ensure project root is in sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_obsidian_theme


def main() -> int:
    # Ensure Windows taskbar uses the application icon
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("InfoHazard.STBEmulatorPro.6.0")
    except Exception:
        pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("STB-Emulator Pro")
    app.setApplicationDisplayName("STB-Emulator Pro by InfoHazard & H7CFoX")
    app.setOrganizationName("InfoHazard & H7CFoX")

    # Set Application Icon
    icon_ico = os.path.join(APP_DIR, "assets", "app_icon.ico")
    icon_png = os.path.join(APP_DIR, "assets", "app_icon.png")
    if os.path.exists(icon_ico):
        app.setWindowIcon(QIcon(icon_ico))
    elif os.path.exists(icon_png):
        app.setWindowIcon(QIcon(icon_png))

    apply_obsidian_theme(app, scale_factor=1.0)

    win = MainWindow()
    if win.config_mgr.get("start_maximized", True):
        win.showMaximized()
    else:
        win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
