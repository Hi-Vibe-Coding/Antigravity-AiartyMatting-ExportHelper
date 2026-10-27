"""
Application Entry Point for Antigravity-AiartyMatting-ExportHelper (AiartyMatting导出助手)
"""
import sys
import os
from pathlib import Path

# 将项目根目录添加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from src.ui.main_window import MainWindow
from src.config import APP_NAME_CN


def setup_high_dpi():
    """配置高分屏 DPI 自适应支持"""
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


def main():
    setup_high_dpi()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME_CN)

    # 自动跟随 Windows 系统的深色/浅色偏好
    setTheme(Theme.AUTO)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
